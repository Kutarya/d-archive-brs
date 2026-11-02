from typing import List, Tuple, Optional
from .base_effect import BaseEffect

class StaticColor(BaseEffect):
    """
    A simple effect that applies a single static color to all LEDs.
    """

    def __init__(self, color: Tuple[int, int, int], name: str = "Static Color"):
        """
        Initialize the StaticColor effect.

        Args:
            color: (R, G, B) tuple for the color (0-255).
            name: Human-readable name.
        """
        super().__init__(name=name, speed=0.0)
        self.color = color

    def apply(self, led_count: int, led_positions: Optional[List[Tuple[float, float]]] = None) -> List[Tuple[int, int, int]]:
        """
        Returns the same color for all LEDs.
        """
        return [self.color] * led_count
