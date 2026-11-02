import math

from .base_effect import BaseEffect


class Wave(BaseEffect):
    EFFECT_ID = "wave"
    PARAMS = {
        "color": {"type": "color"},
        "speed": {"type": "number", "range": [0, 20]},
        "direction": {"type": "choice", "choices": ["vertical", "horizontal"]},
        "wave_length": {"type": "number", "range": [0.1, 10]},
        "enabled": {"type": "boolean"},
    }

    def __init__(self, color=(255, 0, 0), direction="vertical", speed=1.0, wave_length=0.5):
        super().__init__(name="Wave", speed=speed)
        for name, value in self.validate_parameters(
            {"color": color, "direction": direction, "wave_length": wave_length}
        ).items():
            setattr(self, name, value)

    def apply(self, led_count, led_positions=None):
        with self._lock:
            phase = self.get_time()
            colors = []
            for index in range(led_count):
                x, y = led_positions[index] if led_positions and index < len(led_positions) else (0, 0)
                position = x if self.direction == "horizontal" else y
                brightness = (math.sin((phase - position / self.wave_length) * math.tau) + 1) / 2
                colors.append(tuple(int(channel * brightness) for channel in self.color))
            return colors
