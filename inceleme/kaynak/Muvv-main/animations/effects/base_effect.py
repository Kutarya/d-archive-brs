from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import time

class BaseEffect(ABC):
    """
    Abstract Base Class for all visual effects in the Vitray Engine.
    
    An effect is a self-contained unit of logic that generates visual data (Colors or Masks)
    based on time and optional spatial parameters.
    """

    def __init__(self, name: str = "BaseEffect", speed: float = 1.0):
        """
        Initialize the effect.

        Args:
            name: Human-readable name for the effect (e.g., "Rainbow Wave").
            speed: Animation speed multiplier (1.0 = normal, 2.0 = double speed).
        """
        self.name = name
        self.speed = speed
        self._start_time = time.time()
        self.enabled = True

    def update_parameters(self, **kwargs) -> None:
        """
        Updates the effect parameters dynamically.

        Args:
            **kwargs: Key-value pairs of parameters to update.
                      Example: update_parameters(speed=2.0, color=(0, 255, 0))
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                pass # Or log warning: Parameter not found

    def reset(self) -> None:
        """
        Resets the internal state of the effect.
        Useful for restarting animations from the beginning.
        """
        self._start_time = time.time()

    def get_time(self) -> float:
        """
        Returns the elapsed time since start (or reset), scaled by speed.
        """
        return (time.time() - self._start_time) * self.speed

    @abstractmethod
    def apply(self, led_count: int, led_positions: Optional[List[Tuple[float, float]]] = None) -> List[Tuple[int, int, int]]:
        """
        Calculates the colors for the current frame.

        Args:
            led_count: The number of LEDs/Zones to generate colors for.
            led_positions: (Optional) A list of (x, y) coordinates for each LED,
                           normalized between 0.0 and 1.0. Used for spatial effects.

        Returns:
            A list of (R, G, B) tuples, one for each LED/Zone.
            Each channel should be in the range 0-255.
        """
        pass
