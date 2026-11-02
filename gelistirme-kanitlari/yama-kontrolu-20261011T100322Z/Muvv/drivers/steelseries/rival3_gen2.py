"""SteelSeries Rival 3 Gen 2 Wired, HID interface 3."""

import importlib
from copy import deepcopy

from animations.maps import ZoneMap
from drivers.base_mouse import BaseMouse
from managers.errors import TransportError, UnknownDeviceState, ValidationError
from managers.validator import integer, key_code, rgb


class Rival3Gen2Mouse(BaseMouse):
    DISPLAY_NAME = "SteelSeries Rival 3 Gen 2"
    VENDOR_ID = 0x1038
    PRODUCT_ID = 0x1870
    INTERFACE_NUM = 3
    CMD_SET_DPI = 0x34
    CMD_SET_POLLING_RATE = 0x2B
    CMD_SAVE_MEMORY = 0x11
    CMD_SET_COLOR = 0x21
    CMD_SET_BUTTONS = 0x2A
    SC_DPI_LEVELS = 0x05
    TYPE_KEYBOARD_KEY = 0x51

    DPI_MAP = {
        200: 0x04,
        300: 0x06,
        400: 0x08,
        500: 0x0B,
        600: 0x0D,
        700: 0x0F,
        800: 0x12,
        900: 0x14,
        1000: 0x16,
        1100: 0x19,
        1200: 0x1B,
        1300: 0x1D,
        1400: 0x20,
        1500: 0x22,
        1600: 0x24,
        1700: 0x27,
        1800: 0x29,
        1900: 0x2B,
        2000: 0x2E,
        2100: 0x30,
        2200: 0x32,
        2300: 0x34,
        2400: 0x37,
        2500: 0x39,
        2600: 0x3B,
        2700: 0x3E,
        2800: 0x40,
        2900: 0x42,
        3000: 0x45,
        3100: 0x47,
        3200: 0x49,
        3300: 0x4C,
        3400: 0x4E,
        3500: 0x50,
        3600: 0x53,
        3700: 0x55,
        3800: 0x57,
        3900: 0x5A,
        4000: 0x5C,
        4100: 0x5E,
        4200: 0x61,
        4300: 0x63,
        4400: 0x65,
        4500: 0x68,
        4600: 0x6A,
        4700: 0x6C,
        4800: 0x6F,
        4900: 0x71,
        5000: 0x73,
        5100: 0x76,
        5200: 0x78,
        5300: 0x7A,
        5400: 0x7D,
        5500: 0x7F,
        5600: 0x81,
        5700: 0x84,
        5800: 0x86,
        5900: 0x88,
        6000: 0x8B,
        6100: 0x8D,
        6200: 0x8F,
        6300: 0x92,
        6400: 0x94,
        6500: 0x96,
        6600: 0x99,
        6700: 0x9B,
        6800: 0x9D,
        6900: 0xA0,
        7000: 0xA2,
        7100: 0xA4,
        7200: 0xA7,
        7300: 0xA9,
        7400: 0xAB,
        7500: 0xAD,
        7600: 0xB0,
        7700: 0xB2,
        7800: 0xB4,
        7900: 0xB7,
        8000: 0xB9,
        8100: 0xBC,
        8200: 0xBE,
        8300: 0xC0,
        8400: 0xC3,
        8500: 0xC5,
    }
    POLLING_RATE_MAP = {1000: 0x01, 500: 0x02, 250: 0x03, 125: 0x04}
    BUTTON_MAP = {
        "button1": 1,
        "button2": 6,
        "button3": 11,
        "button4": 16,
        "button5": 21,
        "dpi": 26,
        "scrollup": 31,
        "scrolldown": 36,
    }
    DEFAULT_BUTTONS = {
        "button1": 1,
        "button2": 2,
        "button3": 3,
        "button4": 4,
        "button5": 5,
        "dpi": 0x30,
        "scrollup": 0x31,
        "scrolldown": 0x32,
    }
    DEFAULT_DPI = [400, 800, 1200, 2400, 3200]
    MOUSE_FUNCTIONS = frozenset((0, 1, 2, 3, 4, 5, 0x30, 0x31, 0x32))
    ZONE_MAP = {"wheel": 0x01, "middle": 0x02, "underglow": 0x04}
    LED_COORDINATES = {"wheel": (0.5, 0.1), "middle": (0.5, 0.5), "underglow": (0.5, 0.9)}
    CAPABILITIES = {
        "dpi": {"type": "stages", "max_stages": 5, "supported_values": list(DPI_MAP)},
        "polling_rates": list(POLLING_RATE_MAP),
        "rgb": {
            "supported": True,
            "zones": list(ZONE_MAP),
            "effects": ["static", "breathing", "wave", "spectrum"],
            "has_brightness": False,
        },
        "programmable_buttons": 6,
        "button_names": list(BUTTON_MAP),
        "keyboard_usage_ranges": [[4, 164], [224, 231]],
        "macro_support": False,
        "hardware_readback": False,
    }

    def __init__(self, device_path=None):
        super().__init__(self.VENDOR_ID, self.PRODUCT_ID, max_fps=30, device_path=device_path)
        self.led_state = {zone: (0, 0, 0) for zone in self.ZONE_MAP}
        self.dpi_levels = self.DEFAULT_DPI.copy()
        self.active_dpi_index = 0
        self.polling_rate = 1000
        self.button_config = self.DEFAULT_BUTTONS.copy()
        self.zone_mask = sum(self.ZONE_MAP.values())
        self._known = set()

    def connect(self):
        if self._worker_thread and self._worker_thread.is_alive():
            raise TransportError("USB worker is already active.")
        handle = None
        try:
            hid = importlib.import_module("hid")
            if self.device_path is None:
                devices = [
                    entry
                    for entry in hid.enumerate(self.VENDOR_ID, self.PRODUCT_ID)
                    if entry.get("interface_number") == self.INTERFACE_NUM
                ]
                if len(devices) != 1:
                    raise TransportError("Select a device path when zero or multiple Rival mice are present.")
                self.device_path = devices[0]["path"]
            handle = hid.device()
            handle.open_path(self.device_path)
            handle.set_nonblocking(1)
            self.device = handle
            self.is_connected = True
            self._known.clear()
            self._state_uncertain = False
            self._start_worker()
        except Exception as error:
            if handle is not None:
                handle.close()
            self.device = None
            self.is_connected = False
            if isinstance(error, ModuleNotFoundError):
                raise TransportError("hidapi is not installed. Install the hardware dependency.") from error
            raise TransportError(f"Cannot open Rival 3 Gen 2: {error}") from error

    def _require_state(self):
        if self._state_uncertain:
            raise UnknownDeviceState(
                "A previous USB operation was incomplete. Reconnect before changing settings."
            )

    @staticmethod
    def _save_packet():
        return bytes([0x11]) + bytes(63)

    @classmethod
    def _dpi_packet(cls, stages, active):
        integer(active, "DPI stage", 0, 4)
        if not isinstance(stages, (list, tuple)) or len(stages) != 5:
            raise ValidationError("DPI stages must contain exactly five integers.")
        packet = bytearray(64)
        packet[:3] = bytes((cls.CMD_SET_DPI, cls.SC_DPI_LEVELS, active))
        for index, dpi in enumerate(stages):
            integer(dpi, "DPI")
            if dpi not in cls.DPI_MAP:
                raise ValidationError(f"Unsupported DPI: {dpi}. Use 200–8500 in steps of 100.")
            packet[3 + index * 2 : 5 + index * 2] = bytes([cls.DPI_MAP[dpi]]) * 2
        return bytes(packet)

    @classmethod
    def _buttons_packet(cls, mapping):
        if not isinstance(mapping, dict) or set(mapping) != set(cls.BUTTON_MAP):
            raise ValidationError("A full mapping must contain every declared button exactly once.")
        normalized = {}
        packet = bytearray(64)
        packet[0] = cls.CMD_SET_BUTTONS
        for button, value in mapping.items():
            offset = cls.BUTTON_MAP[button]
            if type(value) is int and value in cls.MOUSE_FUNCTIONS:
                normalized[button] = value
                packet[offset] = value
            elif isinstance(value, (tuple, list)) and len(value) == 2:
                if type(value[0]) is not int or value[0] != cls.TYPE_KEYBOARD_KEY:
                    raise ValidationError("Only keyboard assignments (0x51) are supported.")
                normalized[button] = (cls.TYPE_KEYBOARD_KEY, key_code(value[1]))
                packet[offset : offset + 2] = bytes(normalized[button])
            else:
                raise ValidationError(f"Invalid assignment for {button}.")
        if 1 not in normalized.values():
            raise ValidationError("Keep at least one button assigned to left click (0x01).")
        return bytes(packet), normalized

    def _color_packet(self, colors):
        if not isinstance(colors, dict) or set(colors) != set(self.ZONE_MAP):
            raise ValidationError("Colors must contain every LED zone exactly once.")
        normalized = {zone: rgb(color) for zone, color in colors.items()}
        packet = bytearray(64)
        packet[:2] = bytes((self.CMD_SET_COLOR, self.zone_mask))
        for index, zone in enumerate(self.ZONE_MAP):
            packet[2 + index * 3 : 5 + index * 3] = bytes(normalized[zone])
        return bytes(packet), normalized

    def set_color(self, led_zone, color):
        if led_zone not in self.ZONE_MAP:
            raise ValidationError(f"Unknown LED zone: {led_zone!r}.")
        color = rgb(color)
        with self.lock:
            self.led_state[led_zone] = color

    def set_colors(self, colors, wait=True):
        packet, normalized = self._color_packet(colors)
        with self.lock:
            self._require_state()
            if wait:
                receipt = self.transact(((packet, 0),), replace_frame=True)
                self.led_state = normalized
                self._known.add("colors")
                return receipt
            self.submit_frame(packet)
            self.led_state = normalized

    def flush(self):
        with self.lock:
            packet, _ = self._color_packet(self.led_state)
            self.submit_frame(packet)

    def set_dpi(self, level_index, initialize=False):
        integer(level_index, "DPI stage", 0, 4)
        if type(initialize) is not bool:
            raise ValidationError("Initialize must be a boolean.")
        with self.lock:
            self._require_state()
            if "dpi" not in self._known and not initialize:
                raise UnknownDeviceState(
                    "DPI slots have not been read. Set all five slots or explicitly initialize defaults."
                )
            stages = self.dpi_levels if "dpi" in self._known else self.DEFAULT_DPI
            receipt = self.transact(((self._dpi_packet(stages, level_index), 0),))
            self.dpi_levels = list(stages)
            self.active_dpi_index = level_index
            self._known.add("dpi")
            return receipt

    def set_dpi_stages(self, new_stages_list, active=None):
        with self.lock:
            self._require_state()
            if active is None:
                active = self.active_dpi_index
            packet = self._dpi_packet(new_stages_list, active)
            receipt = self.transact(((packet, 0),))
            self.dpi_levels = list(new_stages_list)
            self.active_dpi_index = active
            self._known.add("dpi")
            return receipt

    def set_polling_rate(self, hz):
        integer(hz, "Polling rate")
        if hz not in self.POLLING_RATE_MAP:
            raise ValidationError(f"Unsupported polling rate: {hz}.")
        packet = bytes((self.CMD_SET_POLLING_RATE, self.POLLING_RATE_MAP[hz])) + bytes(62)
        with self.lock:
            self._require_state()
            receipt = self.transact(((packet, 0),))
            self.polling_rate = hz
            self._known.add("polling_rate")
            return receipt

    def save_profile(self):
        with self.lock:
            self._require_state()
            reports = []
            if "colors" in self._known:
                packet, _ = self._color_packet(self.led_state)
                reports.append((packet, 0))
            reports.append((self._save_packet(), 0))
            receipt = self.transact(reports, replace_frame="colors" in self._known)
            return {**receipt, "persistence_requested": True}

    def set_buttons(self, mapping, initialize=False, persist=True):
        if not isinstance(mapping, dict) or not mapping or mapping.keys() - self.BUTTON_MAP.keys():
            raise ValidationError("Mapping contains no buttons or an unknown button.")
        if type(initialize) is not bool or type(persist) is not bool:
            raise ValidationError("Initialize and persist must be booleans.")
        with self.lock:
            self._require_state()
            if "buttons" not in self._known and set(mapping) != set(self.BUTTON_MAP) and not initialize:
                raise UnknownDeviceState(
                    "Button assignments have not been read. Supply a full mapping or explicitly initialize defaults."
                )
            proposed = dict(self.button_config if "buttons" in self._known else self.DEFAULT_BUTTONS)
            proposed.update(mapping)
            packet, proposed = self._buttons_packet(proposed)
            reports = [(packet, 0.05)]
            if persist:
                reports.append((self._save_packet(), 0))
            receipt = self.transact(reports)
            self.button_config = proposed
            self._known.add("buttons")
            return {**receipt, "persistence_requested": persist}

    def bind_key(self, button, usage, initialize=False, persist=True):
        return self.set_buttons({button: (self.TYPE_KEYBOARD_KEY, key_code(usage))}, initialize, persist)

    def restore_buttons(self, persist=True):
        return self.set_buttons(self.DEFAULT_BUTTONS, persist=persist)

    def get_profile(self):
        with self.lock:
            settings = {}
            if "dpi" in self._known:
                settings["dpi"] = {"stages": self.dpi_levels.copy(), "active": self.active_dpi_index}
            if "polling_rate" in self._known:
                settings["polling_rate"] = self.polling_rate
            if "buttons" in self._known:
                settings["buttons"] = deepcopy(self.button_config)
            if "colors" in self._known:
                settings["colors"] = deepcopy(self.led_state)
            return {
                "settings": settings,
                "unknown_fields": sorted({"dpi", "polling_rate", "buttons", "colors"} - self._known),
                "readback_verified": False,
                "state_uncertain": self._state_uncertain,
            }

    def validate_settings(self, settings):
        if (
            not isinstance(settings, dict)
            or not settings
            or settings.keys() - {"dpi", "polling_rate", "buttons", "colors"}
        ):
            raise ValidationError("Profile contains empty or unknown device settings.")
        reports, normalized = [], {}
        if "dpi" in settings:
            dpi = settings["dpi"]
            if not isinstance(dpi, dict) or set(dpi) != {"stages", "active"}:
                raise ValidationError("DPI profile must contain stages and active.")
            reports.append((self._dpi_packet(dpi["stages"], dpi["active"]), 0))
            normalized["dpi"] = {"stages": list(dpi["stages"]), "active": dpi["active"]}
        if "polling_rate" in settings:
            hz = integer(settings["polling_rate"], "Polling rate")
            if hz not in self.POLLING_RATE_MAP:
                raise ValidationError(f"Unsupported polling rate: {hz}.")
            reports.append((bytes((self.CMD_SET_POLLING_RATE, self.POLLING_RATE_MAP[hz])) + bytes(62), 0))
            normalized["polling_rate"] = hz
        if "buttons" in settings:
            packet, normalized["buttons"] = self._buttons_packet(settings["buttons"])
            reports.append((packet, 0.05))
        if "colors" in settings:
            packet, normalized["colors"] = self._color_packet(settings["colors"])
            reports.append((packet, 0))
        return reports, normalized

    def apply_settings(self, settings, persist=False):
        reports, proposed = self.validate_settings(settings)
        if type(persist) is not bool:
            raise ValidationError("Persist must be a boolean.")
        if persist:
            reports.append((self._save_packet(), 0))
        with self.lock:
            self._require_state()
            receipt = self.transact(reports, replace_frame="colors" in proposed)
            if "dpi" in proposed:
                self.dpi_levels = proposed["dpi"]["stages"]
                self.active_dpi_index = proposed["dpi"]["active"]
            if "polling_rate" in proposed:
                self.polling_rate = proposed["polling_rate"]
            if "buttons" in proposed:
                self.button_config = proposed["buttons"]
            if "colors" in proposed:
                self.led_state = proposed["colors"]
            self._known.update(proposed)
            return {**receipt, "persistence_requested": persist}

    def get_zone_map(self):
        return ZoneMap(self.LED_COORDINATES)
