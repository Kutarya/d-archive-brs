import colorsys

from .base_effect import BaseEffect


class SpectrumCycle(BaseEffect):
    EFFECT_ID = "spectrum"
    PARAMS = {
        "speed": {"type": "number", "range": [0, 20]},
        "brightness": {"type": "number", "range": [0, 1]},
        "enabled": {"type": "boolean"},
    }

    def __init__(self, speed=1.0, brightness=1.0):
        super().__init__(name="Spectrum Cycle", speed=speed)
        self.brightness = self.validate_parameters({"brightness": brightness})["brightness"]

    def apply(self, led_count, led_positions=None):
        with self._lock:
            color = colorsys.hsv_to_rgb((self.get_time() / 6) % 1, 1, self.brightness)
            return [tuple(round(channel * 255) for channel in color)] * led_count
