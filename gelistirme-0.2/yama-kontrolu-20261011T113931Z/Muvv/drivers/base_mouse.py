import logging
import queue
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import Future, TimeoutError
from copy import deepcopy
from dataclasses import dataclass

from managers.errors import DeviceBusy, OperationTimeout, TransportError, ValidationError
from managers.validator import number

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class WriteTransaction:
    packets: tuple
    future: Future


class BaseMouse(ABC):
    CAPABILITIES = {}
    ZONE_MAP = {}
    QUEUE_LIMIT = 64
    WRITE_TIMEOUT = 1.5

    def __init__(self, vendor_id, product_id, max_fps=30, device_path=None):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.max_fps = max_fps
        self.device_path = device_path
        self.is_connected = False
        self.device = None
        self.lock = threading.RLock()
        self.command_queue = queue.Queue(maxsize=self.QUEUE_LIMIT)
        self._work = threading.Condition()
        self._worker_thread = None
        self._closing = False
        self._frame = None
        self._state_uncertain = False
        self._last_error = None
        self._writes = 0
        self._frames_replaced = 0

    def get_capabilities(self):
        return deepcopy(self.CAPABILITIES)

    def _start_worker(self):
        with self._work:
            if self._worker_thread and self._worker_thread.is_alive():
                raise TransportError("The previous USB worker is still active.")
            self._closing = False
            self._last_error = None
            self._worker_thread = threading.Thread(
                target=self._worker_loop, name=f"muvv-usb-{self.product_id:04x}", daemon=True
            )
            self._worker_thread.start()

    @staticmethod
    def _validate_packets(packets):
        result = []
        for data, delay in packets:
            if len(result) == 16:
                raise ValidationError("A USB transaction must contain 1–16 reports.")
            if not isinstance(data, bytes) or not data:
                raise ValidationError("USB reports must be nonempty bytes.")
            number(delay, "USB inter-report delay", 0, 1)
            result.append((data, delay))
        if not result or len(result) > 16:
            raise ValidationError("A USB transaction must contain 1–16 reports.")
        return tuple(result)

    def submit(self, packets, replace_frame=False):
        transaction = WriteTransaction(self._validate_packets(packets), Future())
        with self._work:
            if (
                self._closing
                or not self.is_connected
                or not self._worker_thread
                or not self._worker_thread.is_alive()
            ):
                raise TransportError("Device is not connected.")
            try:
                self.command_queue.put_nowait(transaction)
            except queue.Full as error:
                raise TransportError(
                    "USB command queue is full; retry after pending commands finish."
                ) from error
            if replace_frame:
                self._frame = None
            self._work.notify()
        return transaction.future

    def transact(self, packets, replace_frame=False):
        future = self.submit(packets, replace_frame=replace_frame)
        try:
            return future.result(timeout=self.WRITE_TIMEOUT)
        except TimeoutError as error:
            if future.cancel():
                raise DeviceBusy(
                    "USB queue wait timed out. This operation was cancelled before writing."
                ) from error
            with self._work:
                self._state_uncertain = True
                self._last_error = "USB write exceeded its deadline. Reconnect after the worker closes."
                self.is_connected = False
                self._closing = True
                self._frame = None
                self._work.notify_all()
            raise OperationTimeout(
                "USB write timed out. The device may have received part of the operation."
            ) from error

    def submit_frame(self, packet):
        packet = self._validate_packets(((packet, 0),))[0][0]
        with self._work:
            if self._closing or not self.is_connected:
                raise TransportError("Device is not connected.")
            if self._frame is not None:
                self._frames_replaced += 1
            self._frame = packet
            self._work.notify()

    def _write(self, packet):
        if not self.is_connected or self.device is None:
            raise TransportError("Device disconnected before the write.")
        count = self.device.write(packet)
        if type(count) is not int or count < len(packet):
            raise TransportError(f"Incomplete USB write ({count!r}/{len(packet)} bytes).")
        self._writes += 1
        return count

    def _worker_loop(self):
        try:
            while True:
                transaction = None
                with self._work:
                    self._work.wait_for(
                        lambda: self._closing or not self.command_queue.empty() or self._frame is not None
                    )
                    if self._closing:
                        break
                    try:
                        transaction = self.command_queue.get_nowait()
                    except queue.Empty:
                        packet, self._frame = self._frame, None
                try:
                    if transaction is not None:
                        if not transaction.future.set_running_or_notify_cancel():
                            continue
                        counts = []
                        for packet, delay in transaction.packets:
                            counts.append(self._write(packet))
                            if delay:
                                time.sleep(delay)
                        transaction.future.set_result(
                            {
                                "transport": "written",
                                "reports": len(counts),
                                "bytes_written": sum(counts),
                                "readback_verified": False,
                            }
                        )
                    else:
                        self._write(packet)
                except Exception as error:
                    self._state_uncertain = True
                    self._last_error = str(error)
                    self.is_connected = False
                    if transaction is not None and not transaction.future.done():
                        transaction.future.set_exception(TransportError(str(error)))
                    LOG.warning("USB write failed: %s", error)
                    with self._work:
                        self._closing = True
                        self._frame = None
                    break
                finally:
                    if transaction is not None:
                        self.command_queue.task_done()
        finally:
            with self._work:
                self._frame = None
                while True:
                    try:
                        pending = self.command_queue.get_nowait()
                    except queue.Empty:
                        break
                    if not pending.future.done():
                        pending.future.set_exception(TransportError("Device is closing."))
                    self.command_queue.task_done()
            handle, self.device = self.device, None
            self.is_connected = False
            if handle is not None:
                try:
                    handle.close()
                except Exception as error:
                    self._last_error = str(error)
                    LOG.warning("USB close failed: %s", error)

    def disconnect(self, timeout=2.0):
        with self._work:
            self._closing = True
            self._frame = None
            self._work.notify_all()
        worker = self._worker_thread
        if worker and worker is not threading.current_thread():
            worker.join(timeout)
        if worker and worker.is_alive():
            self._state_uncertain = True
            self._last_error = "USB backend is still blocked; handle will close when the write returns."
            return False
        if self.device is not None:
            self.device.close()
            self.device = None
        self.is_connected = False
        return True

    def status(self):
        with self._work:
            return {
                "connected": self.is_connected,
                "pending_commands": self.command_queue.qsize(),
                "pending_frame": self._frame is not None,
                "frames_replaced": self._frames_replaced,
                "reports_written": self._writes,
                "state_uncertain": self._state_uncertain,
                "last_error": self._last_error,
                "worker_alive": bool(self._worker_thread and self._worker_thread.is_alive()),
                "closing": self._closing,
            }

    def reconnect(self):
        if not self.disconnect():
            raise TransportError("Cannot reconnect while the previous USB write is blocked.")
        self.connect()

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def set_color(self, led_zone, color):
        pass

    @abstractmethod
    def set_dpi(self, level, initialize=False):
        pass

    @abstractmethod
    def save_profile(self):
        pass

    @abstractmethod
    def flush(self):
        pass
