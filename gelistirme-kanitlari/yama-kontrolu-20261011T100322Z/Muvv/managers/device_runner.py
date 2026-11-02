import logging
import threading
import time
from contextlib import contextmanager
from copy import deepcopy

from animations.effect_registry import create_effect
from animations.layer import Layer
from animations.vitray import Vitray
from managers.errors import DeviceBusy, TransportError, ValidationError

LOG = logging.getLogger(__name__)


class DeviceRunner:
    def __init__(self, driver_class, device_path=None):
        self.driver_class = driver_class
        self.device_path = device_path
        self.driver = driver_class(device_path=device_path)
        self.engine = None
        self.zone_map = None
        self._stop_event = threading.Event()
        self._thread = None
        self._command_lock = threading.RLock()
        self.is_running = False
        self.last_error = None

    def start(self):
        with self._command_lock:
            if self.is_running:
                return True
            try:
                self.driver.connect()
                if not self.driver.is_connected:
                    raise TransportError("Driver did not connect.")
                self.zone_map = self.driver.get_zone_map()
                self.engine = Vitray(self.zone_map)
                self._stop_event.clear()
                self.is_running = True
                self._thread = threading.Thread(target=self._render_loop, name="muvv-render", daemon=True)
                self._thread.start()
                return True
            except Exception:
                self.driver.disconnect()
                self.is_running = False
                raise

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=2)
        with self._command_lock:
            self.is_running = False
            return self.driver.disconnect()

    def _require_connected(self):
        if not self.driver.is_connected or self._stop_event.is_set():
            raise TransportError("Device is disconnected or stopping.")

    @contextmanager
    def _command(self):
        if not self._command_lock.acquire(timeout=1):
            raise DeviceBusy("Device is busy. No new command was sent; retry shortly.")
        try:
            yield
        finally:
            self._command_lock.release()

    def _frame(self):
        frame = self.engine.render()
        return {self.zone_map.get_name(index): color for index, color in enumerate(frame)}

    def _render_loop(self):
        interval = 1 / self.driver.max_fps
        previous = None
        while not self._stop_event.is_set():
            start = time.monotonic()
            try:
                # Commands and rendering share a lock so an old frame cannot follow a new setting.
                with self._command_lock:
                    if self.engine.layers and self.driver.is_connected:
                        frame = self._frame()
                        if frame != previous:
                            self.driver.set_colors(frame, wait=False)
                            previous = frame
                    else:
                        previous = None
            except Exception as error:
                self.last_error = str(error)
                LOG.warning("Render failed for %r: %s", self.device_path, error)
                self._stop_event.wait(0.5)
            self._stop_event.wait(max(0, interval - (time.monotonic() - start)))

    def set_effect(self, effect_name, options=None):
        effect = create_effect(effect_name, options)
        with self._command():
            self._require_connected()
            if self.engine is None:
                raise TransportError("Animation engine is not ready.")
            colors = effect.apply(self.zone_map.led_count, self.zone_map.positions)
            frame = dict(zip(self.zone_map.zone_names, colors, strict=True))
            receipt = self.driver.set_colors(frame)
            self.engine.replace_layers([Layer(effect)])
            self.last_error = None
            return {**receipt, "effect": effect.EFFECT_ID}

    def update_effect(self, options):
        with self._command():
            self._require_connected()
            if self.engine is None or len(self.engine.layers) != 1:
                raise ValidationError("Select an effect before updating it.")
            effect = self.engine.layers[0].effect
            values = effect.validate_parameters(options)
            if not values:
                raise ValidationError("Supply at least one effect option.")
            old = effect.parameters()
            with self.engine.lock:
                effect.update_parameters(**values)
                try:
                    receipt = self.driver.set_colors(self._frame())
                except Exception:
                    effect.update_parameters(**old)
                    raise
            return {**receipt, "effect": effect.EFFECT_ID}

    def set_color(self, hex_color):
        return self.set_effect("static", {"color": hex_color})

    def set_dpi(self, level, initialize=False):
        with self._command():
            self._require_connected()
            return self.driver.set_dpi(level, initialize=initialize)

    def set_dpi_stages(self, stages, active=None):
        with self._command():
            self._require_connected()
            return self.driver.set_dpi_stages(stages, active=active)

    def set_polling(self, hz):
        with self._command():
            self._require_connected()
            return self.driver.set_polling_rate(hz)

    def bind_key(self, button, usage, initialize=False, persist=True):
        with self._command():
            self._require_connected()
            return self.driver.bind_key(button, usage, initialize=initialize, persist=persist)

    def restore_buttons(self, persist=True):
        with self._command():
            self._require_connected()
            return self.driver.restore_buttons(persist=persist)

    def save_profile(self):
        with self._command():
            self._require_connected()
            return self.driver.save_profile()

    def reconnect(self):
        if not self.stop():
            raise TransportError("The previous USB write is still blocked.")
        return self.start()

    def get_capabilities(self):
        return self.driver.get_capabilities()

    def get_state(self):
        with self._command():
            effect = None
            if self.engine is not None and len(self.engine.layers) == 1:
                current = self.engine.layers[0].effect
                effect = {"name": current.EFFECT_ID, "options": current.parameters()}
            return {
                **self.driver.get_profile(),
                "effect": effect,
                "transport": self.driver.status(),
                "render_error": self.last_error,
            }

    def host_profile(self, name):
        state = self.get_state()
        if state["state_uncertain"]:
            raise TransportError("Cannot save a profile after an incomplete USB operation.")
        return {
            "version": 1,
            "name": name,
            "device": {"vendor_id": self.driver.vendor_id, "product_id": self.driver.product_id},
            "settings": state["settings"],
            "effect": state["effect"],
            "unknown_fields": state["unknown_fields"],
            "readback_verified": False,
        }

    def apply_profile(self, profile, persist=False):
        from managers.profile_store import validate_profile

        validate_profile(profile)
        expected = {"vendor_id": self.driver.vendor_id, "product_id": self.driver.product_id}
        if profile["device"] != expected:
            raise ValidationError("Profile belongs to a different device model.")
        effect = None
        if profile["effect"] is not None:
            effect = create_effect(profile["effect"]["name"], profile["effect"]["options"])
        settings = deepcopy(profile["settings"])
        if effect is not None:
            colors = effect.apply(self.zone_map.led_count, self.zone_map.positions)
            settings["colors"] = dict(zip(self.zone_map.zone_names, colors, strict=True))
        self.driver.validate_settings(settings)
        with self._command():
            self._require_connected()
            receipt = self.driver.apply_settings(settings, persist=persist)
            if effect is not None:
                self.engine.replace_layers([Layer(effect)])
            elif "colors" in settings:
                self.engine.clear_layers()
            return receipt
