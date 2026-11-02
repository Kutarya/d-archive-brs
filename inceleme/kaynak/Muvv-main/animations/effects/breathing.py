import math
import time
from typing import Tuple, List, Optional
from .base_effect import BaseEffect

class Breathing(BaseEffect):
    """
    A Breathing effect that pulses a color on and off using a sine wave.
    """

    def __init__(self, color: Tuple[int, int, int] = (0, 255, 0), speed: float = 1.0, name: str = "Breathing"):
        """
        Initialize the Breathing effect.

        Args:
            color: The (R, G, B) color to pulse.
            speed: The speed of the breathing effect (cycles per second, roughly).
                   Higher is faster.
            name: Effect name.
        """
        super().__init__(name)
        self.color = color
        self.speed = speed
        self._start_time = time.time()

    def apply(self, led_count: int, led_positions: Optional[List[Tuple[float, float]]] = None) -> List[Tuple[int, int, int]]:
        """
        Generates the breathing color frame.
        """
        current_time = time.time()
        elapsed = current_time - self._start_time
        
        # Calculate brightness using a sine wave
        # sin() goes from -1 to 1. 
        # We want 0.0 to 1.0.
        # Formula: (sin(time * speed) + 1) / 2
        
        # Adjusting speed factor explicitly
        # 2*PI * frequency * time
        # Let's say speed 1.0 = 1 full breath (0->1->0) every 2-3 seconds roughly
        
        val = (math.sin(elapsed * self.speed * 2.0) + 1.0) / 2.0
        
        # Apply brightness to color
        r = int(self.color[0] * val)
        g = int(self.color[1] * val)
        b = int(self.color[2] * val)
        
        return [(r, g, b)] * led_count
