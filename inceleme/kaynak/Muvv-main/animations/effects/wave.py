from typing import List, Tuple, Optional
import math
import time
from .base_effect import BaseEffect

class Wave(BaseEffect):
    """
    A spatial wave effect that moves across the device.
    Uses LED coordinates (X or Y) to calculate phase shift of brightness.
    """

    def __init__(self, color: Tuple[int, int, int] = (255, 0, 0), 
                 direction: str = 'vertical', 
                 speed: float = 1.0, 
                 wave_length: float = 0.5):
        """
        Initialize the Wave effect.

        Args:
            color: The peak color of the wave (R, G, B).
            direction: 'horizontal' (x-axis) or 'vertical' (y-axis).
            speed: How fast the wave moves (cycles per second).
            wave_length: The spatial length of one full wave cycle (0.0 - 1.0 is full device width).
        """
        super().__init__(name="Wave", speed=speed)
        self.color = color
        self.direction = direction.lower()
        self.wave_length = max(0.1, wave_length) # Prevent division by zero

    def apply(self, led_count: int, led_positions: Optional[List[Tuple[float, float]]] = None) -> List[Tuple[int, int, int]]:
        """
        Calculates the colors for the current frame based on time and LED positions.
        """
        t = self.get_time()
        colors = []

        for i in range(led_count):
            # Default to 0.0 if no positions provided
            x, y = (0.0, 0.0)
            if led_positions and i < len(led_positions):
                x, y = led_positions[i]

            # Determine spatial value based on direction
            pos_value = x if self.direction == 'horizontal' else y

            # Calculate Wave Phase
            # Phase = (Time * Speed) - (Position / Wavelength)
            # - Subtracting position makes the wave move FORWARD (positive direction)
            phase = (t * self.speed) - (pos_value / self.wave_length)
            
            # Sine Wave Calculation
            # Map [-1.0, 1.0] to [0.0, 1.0] for brightness
            sine_val = math.sin(phase * 2 * math.pi)
            brightness = (sine_val + 1.0) / 2.0

            r = int(self.color[0] * brightness)
            g = int(self.color[1] * brightness)
            b = int(self.color[2] * brightness)

            colors.append((r, g, b))

        return colors
