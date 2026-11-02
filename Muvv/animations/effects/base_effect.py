import threading
import time
from abc import ABC, abstractmethod

from managers.errors import ValidationError
from managers.validator import number, rgb


class BaseEffect(ABC):
    PARAMS = {}
    EFFECT_ID = "base"

    def __init__(self, name="BaseEffect", speed=1.0):
        self.name = name
        self.speed = number(speed, "Speed", 0, 20)
        self.enabled = True
        self._lock = threading.RLock()
        self._start_time = time.monotonic()
        self._phase = 0.0

    @classmethod
    def validate_parameters(cls, options):
        if not isinstance(options, dict):
            raise ValidationError("Effect options must be an object.")
        unknown = options.keys() - cls.PARAMS.keys()
        if unknown:
            raise ValidationError(f"Unknown {cls.EFFECT_ID} options: {', '.join(sorted(unknown))}.")
        result = {}
        for name, value in options.items():
            if name == "color":
                result[name] = rgb(value)
            elif name == "direction":
                if value not in ("horizontal", "vertical"):
                    raise ValidationError("Direction must be horizontal or vertical.")
                result[name] = value
            elif name == "enabled":
                if type(value) is not bool:
                    raise ValidationError("Enabled must be a boolean.")
                result[name] = value
            else:
                bounds = cls.PARAMS[name]["range"]
                result[name] = number(value, name, *bounds)
        return result

    def update_parameters(self, **kwargs):
        values = self.validate_parameters(kwargs)
        with self._lock:
            if "speed" in values:
                now = time.monotonic()
                self._phase += (now - self._start_time) * self.speed
                self._start_time = now
            for name, value in values.items():
                setattr(self, name, value)

    def parameters(self):
        with self._lock:
            return {name: getattr(self, name) for name in self.PARAMS}

    def reset(self):
        with self._lock:
            self._phase = 0.0
            self._start_time = time.monotonic()

    def get_time(self):
        with self._lock:
            return self._phase + (time.monotonic() - self._start_time) * self.speed

    @abstractmethod
    def apply(self, led_count, led_positions=None):
        pass
