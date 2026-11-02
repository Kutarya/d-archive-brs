from managers.validator import rgb

from .base_effect import BaseEffect


class StaticColor(BaseEffect):
    EFFECT_ID = "static"
    PARAMS = {"color": {"type": "color"}, "enabled": {"type": "boolean"}}

    def __init__(self, color=(255, 255, 255), name="Static Color"):
        super().__init__(name=name, speed=0)
        self.color = rgb(color)

    def apply(self, led_count, led_positions=None):
        with self._lock:
            return [self.color] * led_count
