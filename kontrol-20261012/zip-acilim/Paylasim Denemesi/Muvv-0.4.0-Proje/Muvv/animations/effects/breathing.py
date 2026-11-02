import math

from managers.validator import rgb

from .base_effect import BaseEffect


class Breathing(BaseEffect):
    EFFECT_ID = "breathing"
    PARAMS = {
        "color": {"type": "color"},
        "speed": {"type": "number", "range": [0, 20]},
        "enabled": {"type": "boolean"},
    }

    def __init__(self, color=(0, 255, 0), speed=1.0, name="Breathing"):
        super().__init__(name=name, speed=speed)
        self.color = rgb(color)

    def apply(self, led_count, led_positions=None):
        with self._lock:
            brightness = (math.sin(self.get_time() * 2) + 1) / 2
            return [tuple(int(channel * brightness) for channel in self.color)] * led_count
