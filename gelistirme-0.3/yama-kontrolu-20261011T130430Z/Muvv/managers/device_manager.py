import importlib
import logging
import threading
import time

from managers.device_registry import get_driver_class
from managers.device_runner import DeviceRunner
from managers.errors import AmbiguousDevice, DeviceBusy, DeviceNotFound, MuvvError, TransportError
from managers.ipc_server import IPCServer
from managers.profile_store import ProfileStore, profile_name
from managers.validator import CommandValidator

LOG = logging.getLogger(__name__)


class DeviceManager:
    def __init__(
        self, scan_interval=2.0, enumerate_devices=None, runner_factory=DeviceRunner, profile_directory=None
    ):
        if not 0.1 <= scan_interval <= 60:
            raise ValueError("Scan interval must be between 0.1 and 60 seconds.")
        self.scan_interval = scan_interval
        self._enumerate_devices = enumerate_devices
        self._runner_factory = runner_factory
        self._stop_event = threading.Event()
        self._scan_thread = None
        self._lock = threading.RLock()
        self._scan_lock = threading.Lock()
        self.runners = {}
        self._retry = {}
        self._retired = {}
        self.scan_error = None
        self.ipc_server = IPCServer(device_manager=self)
        self.profile_store = ProfileStore(profile_directory)
        self.is_running = False

    def start(self):
        if self.is_running:
            return
        if self._scan_thread and self._scan_thread.is_alive():
            raise TransportError("The previous HID scan is still closing.")
        with self._lock:
            retired = list(self._retired.items())
        for path, runner in retired:
            if runner.stop(timeout=0):
                with self._lock:
                    self._retired.pop(path, None)
        with self._lock:
            if self._retired:
                raise TransportError("The previous USB workers are still closing.")
        if self._enumerate_devices is None:
            try:
                self._enumerate_devices = importlib.import_module("hid").enumerate
            except ModuleNotFoundError as error:
                raise TransportError("hidapi is missing. Install Muvv's hardware dependency.") from error
        self._stop_event.clear()
        # The socket must be acquired before devices or scanning threads are started.
        self.ipc_server.start()
        try:
            self.is_running = True
            self._scan_thread = threading.Thread(target=self._scan_loop, name="muvv-scan", daemon=True)
            self._scan_thread.start()
        except Exception:
            self.is_running = False
            self._stop_event.set()
            self.ipc_server.stop()
            raise

    def stop(self):
        self._stop_event.set()
        self.ipc_server.stop(release_lock=False)
        if self._scan_thread and self._scan_thread is not threading.current_thread():
            self._scan_thread.join(timeout=2)
        with self._lock:
            runners = list(self.runners.items()) + list(self._retired.items())
            self.runners.clear()
        deadline = time.monotonic() + 2
        for path, runner in runners:
            if not runner.stop(timeout=max(0, deadline - time.monotonic())):
                with self._lock:
                    self._retired[path] = runner
                LOG.warning("USB worker for %r is still closing.", path)
            else:
                with self._lock:
                    self._retired.pop(path, None)
        self.is_running = False
        scan_closed = not (self._scan_thread and self._scan_thread.is_alive())
        with self._lock:
            devices_closed = not self._retired
        return scan_closed and devices_closed and self.ipc_server.release_lock()

    def _scan_loop(self):
        while not self._stop_event.is_set():
            try:
                self._scan_devices()
            except Exception as error:
                self.scan_error = str(error)
                LOG.warning("Device scan failed: %s", error)
            self._stop_event.wait(self.scan_interval)

    @staticmethod
    def _device_id(path):
        if isinstance(path, bytes):
            return path.decode("utf-8", errors="surrogateescape")
        return str(path)

    def _scan_devices(self):
        with self._scan_lock:
            enumerate_devices = self._enumerate_devices
            if enumerate_devices is None:
                enumerate_devices = importlib.import_module("hid").enumerate
            entries = enumerate_devices()
            self.scan_error = None
            devices = {}
            for entry in entries:
                driver = get_driver_class(entry.get("vendor_id"), entry.get("product_id"))
                if (
                    driver is None
                    or entry.get("interface_number") != driver.INTERFACE_NUM
                    or "path" not in entry
                ):
                    continue
                devices[self._device_id(entry["path"])] = (entry["path"], driver)
            with self._lock:
                active = list(self.runners.items())
                retired = list(self._retired.items())
            for path, runner in active:
                if path not in devices or not runner.driver.is_connected:
                    with self._lock:
                        self.runners.pop(path, None)
                    if not runner.stop():
                        with self._lock:
                            self._retired[path] = runner
            for path, runner in retired:
                if runner.stop(timeout=0):
                    with self._lock:
                        self._retired.pop(path, None)
            for path, (raw_path, driver) in sorted(devices.items()):
                if self._stop_event.is_set():
                    return
                with self._lock:
                    if path in self.runners or path in self._retired:
                        continue
                    retry = self._retry.get(path, {})
                if time.monotonic() < retry.get("next_attempt", 0):
                    continue
                runner = self._runner_factory(driver, device_path=raw_path)
                try:
                    if not runner.start():
                        raise TransportError("Runner did not start.")
                    with self._lock:
                        stopping = self._stop_event.is_set()
                        if not stopping:
                            self.runners[path] = runner
                            self._retry.pop(path, None)
                    if stopping:
                        if not runner.stop():
                            with self._lock:
                                self._retired[path] = runner
                        return
                    LOG.info("Connected device %r", path)
                except Exception as error:
                    if not runner.stop():
                        with self._lock:
                            self._retired[path] = runner
                    attempts = retry.get("attempts", 0) + 1
                    with self._lock:
                        self._retry[path] = {
                            "attempts": attempts,
                            "next_attempt": time.monotonic() + min(30, 2 ** min(attempts, 5)),
                            "error": str(error),
                        }
                    LOG.warning("Cannot open %r: %s", path, error)
            with self._lock:
                self._retry = {path: retry for path, retry in self._retry.items() if path in devices}

    def resolve_device_id(self, identifier=None):
        with self._lock:
            active = sorted(self.runners)
            if not active:
                return None
            if identifier is None or str(identifier).strip().lower() in ("", "default", "@default", "first"):
                return active[0]
            query = str(identifier).strip()
            if query in self.runners:
                return query
            if query.isdecimal():
                index = int(query)
                if index == 0:
                    return active[0]
                return active[index - 1] if 1 <= index <= len(active) else None
            matches = [
                path
                for path, runner in self.runners.items()
                if query.casefold() in path.casefold()
                or query.casefold() in type(getattr(runner, "driver", None)).__name__.casefold()
            ]
            if len(matches) > 1:
                raise AmbiguousDevice(
                    f"{identifier!r} matches multiple devices. Use the exact ID or list index."
                )
            return matches[0] if matches else None

    def _runner(self, identifier):
        with self._lock:
            path = self.resolve_device_id(identifier)
            if path is None:
                raise DeviceNotFound(f"Device {identifier!r} not found.")
            return self.runners[path]

    def get_active_devices(self):
        with self._lock:
            return [
                {
                    "index": index,
                    "id": path,
                    "name": getattr(runner.driver, "DISPLAY_NAME", type(runner.driver).__name__),
                    "vendor_id": runner.driver.vendor_id,
                    "product_id": runner.driver.product_id,
                    "connected": runner.driver.is_connected,
                    "session_id": getattr(runner, "session_id", None),
                }
                for index, (path, runner) in enumerate(sorted(self.runners.items()), start=1)
            ]

    def status(self):
        with self._lock:
            return {
                "running": self.is_running,
                "scan_error": self.scan_error,
                "devices": len(self.runners),
                "closing_devices": sorted(self._retired),
                "connection_errors": {path: retry["error"] for path, retry in self._retry.items()},
                "protocol_version": 1,
                "scan_thread_alive": bool(self._scan_thread and self._scan_thread.is_alive()),
            }

    def snapshot(self, identifier=None):
        devices = self.get_active_devices()
        selected = self.resolve_device_id(identifier)
        if selected is None and devices:
            selected = devices[0]["id"]
        info, device_error = None, None
        if selected is not None:
            try:
                runner = self._runner(selected)
                info = {"capabilities": runner.get_capabilities(), "state": runner.get_state()}
            except MuvvError as error:
                device_error = {"code": error.code, "message": str(error)}
        try:
            profiles = self.profile_store.catalog()
        except (MuvvError, OSError) as error:
            profiles = {
                "profiles": [],
                "profile_errors": [{"file": "", "message": str(error)[:160]}],
                "next_offset": None,
                "profile_count": 0,
                "profile_limit_exceeded": False,
            }
        return {
            "devices": devices,
            "selected_device": selected,
            "info": info,
            "device_error": device_error,
            "daemon": self.status(),
            **profiles,
        }

    def set_device_effect(self, device_id, effect_name, options=None, **session):
        return self._runner(device_id).set_effect(effect_name, options, **session)

    def update_device_effect(self, device_id, options, **session):
        return self._runner(device_id).update_effect(options, **session)

    def set_device_color(self, device_id, hex_color, **session):
        return self._runner(device_id).set_color(hex_color, **session)

    def set_device_colors(self, device_id, colors, **session):
        return self._runner(device_id).set_colors(colors, **session)

    def stop_device_effect(self, device_id, **session):
        return self._runner(device_id).stop_effect(**session)

    def set_device_dpi(self, device_id, level, initialize=False, **session):
        runner = self._runner(device_id)
        valid, message = CommandValidator.validate_dpi(runner.get_capabilities(), level)
        if not valid:
            return False, message
        return (
            runner.set_dpi(level, initialize=True, **session)
            if initialize
            else runner.set_dpi(level, **session)
        )

    def set_device_dpi_stages(self, device_id, stages, active=None, **session):
        return self._runner(device_id).set_dpi_stages(stages, active, **session)

    def set_device_polling(self, device_id, hz, **session):
        runner = self._runner(device_id)
        valid, message = CommandValidator.validate_polling(runner.get_capabilities(), hz)
        if not valid:
            return False, message
        return runner.set_polling(hz, **session)

    def bind_device_key(self, device_id, button, key_code, initialize=False, persist=True, **session):
        runner = self._runner(device_id)
        CommandValidator.require(CommandValidator.validate_button(runner.get_capabilities(), button))
        return runner.bind_key(button, key_code, initialize, persist, **session)

    def restore_device_buttons(self, device_id, persist=True, **session):
        return self._runner(device_id).restore_buttons(persist, **session)

    def set_device_button(self, device_id, button, assignment, initialize=False, persist=False, **session):
        runner = self._runner(device_id)
        CommandValidator.require(CommandValidator.validate_button(runner.get_capabilities(), button))
        return runner.set_button(button, assignment, initialize, persist, **session)

    def save_device_profile(self, device_id, **session):
        return self._runner(device_id).save_profile(**session)

    def reconnect_device(self, device_id, **session):
        if not self._scan_lock.acquire(timeout=1):
            raise DeviceBusy("A device scan is in progress. Retry after it finishes.")
        try:
            return self._runner(device_id).reconnect(**session)
        finally:
            self._scan_lock.release()

    def get_device_capabilities(self, device_id):
        try:
            return self._runner(device_id).get_capabilities()
        except DeviceNotFound:
            return None

    def get_device_state(self, device_id):
        runner = self._runner(device_id)
        return runner.get_state() if hasattr(runner, "get_state") else {}

    def save_host_profile(self, device_id, name, overwrite=False, **session):
        name = profile_name(name)
        return self.profile_store.save(self._runner(device_id).host_profile(name, **session), overwrite)

    def apply_host_profile(self, device_id, name, persist=False, **session):
        profile = self.profile_store.load(name)
        return self._runner(device_id).apply_profile(profile, persist, **session)
