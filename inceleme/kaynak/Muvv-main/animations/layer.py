from typing import List, Tuple, Optional
from animations.effects.base_effect import BaseEffect

class Layer:
    """
    Represents a single layer in the Vitray Animation Engine.
    
    A layer holds an Effect and properties like Opacity and Blending Mode.
    It takes the background color (from layers below it) and blends its own
    effect output on top of it.
    """

    def __init__(self, effect: BaseEffect, opacity: float = 1.0, enabled: bool = True, blending_mode: str = 'normal', target_zones: Optional[List[int]] = None):
        """
        Initialize the Layer.

        Args:
            effect: The BaseEffect instance to run on this layer.
            opacity: Transparency level (0.0 = invisible, 1.0 = fully visible).
            enabled: If False, this layer is skipped during rendering.
            blending_mode: How to mix with the background. 
                           Supported: 'normal' (replace), 'add' (additive), 'multiply'.
            target_zones: Optional list of LED indices to apply this effect on.
                          If None, effect applies to ALL LEDs.
        """
        self.effect = effect
        self.opacity = max(0.0, min(1.0, opacity)) # Clamp between 0.0 and 1.0
        self.enabled = enabled
        self.blending_mode = blending_mode.lower()
        self.target_zones = target_zones # Indices of LEDs to affect

    def process(self, background_buffer: List[Tuple[int, int, int]], led_count: int, led_positions: Optional[List[Tuple[float, float]]] = None) -> List[Tuple[int, int, int]]:
        """
        Processes the layer and blends it with the background buffer.

        Args:
            background_buffer: The list of (R, G, B) colors from underlying layers.
            led_count: Number of LEDs to process.
            led_positions: (Optional) Spatial positions for the effect.

        Returns:
            A new list of (R, G, B) colors representing the result of this layer + background.
        """
        
        # 1. If disabled or fully transparent, just return the background
        if not self.enabled or self.opacity <= 0.0:
            return background_buffer

        # 2. Generate colors from the Effect
        # Note: We pass led_count explicitly to the effect
        layer_colors = self.effect.apply(led_count, led_positions)

        # 3. Blend with Background
        result_buffer = []
        
        for i in range(led_count):
            # Check if this LED is targeted
            if self.target_zones is not None and i not in self.target_zones:
                # Skip processing for this LED (keep background color)
                result_buffer.append(background_buffer[i])
                continue

            bg_r, bg_g, bg_b = background_buffer[i]
            
            # Handle case where effect might return fewer colors than led_count (safety)
            if i < len(layer_colors):
                fg_r, fg_g, fg_b = layer_colors[i]
            else:
                fg_r, fg_g, fg_b = (0, 0, 0)

            # Apply Opacity to Foreground
            # (In 'normal' blending, opacity acts as alpha interpolation)
            
            out_r, out_g, out_b = bg_r, bg_g, bg_b

            if self.blending_mode == 'normal':
                # Normal Blending (Alpha Compositing)
                # Out = FG * Alpha + BG * (1 - Alpha)
                out_r = (fg_r * self.opacity) + (bg_r * (1.0 - self.opacity))
                out_g = (fg_g * self.opacity) + (bg_g * (1.0 - self.opacity))
                out_b = (fg_b * self.opacity) + (bg_b * (1.0 - self.opacity))

            elif self.blending_mode == 'add':
                # Additive Blending (Linear Dodge)
                # Out = BG + (FG * Opacity)
                out_r = bg_r + (fg_r * self.opacity)
                out_g = bg_g + (fg_g * self.opacity)
                out_b = bg_b + (fg_b * self.opacity)

            elif self.blending_mode == 'multiply':
                # Multiply Blending 
                # Out = (BG * FG) / 255 * Opacity + BG * (1 - Opacity)
                # Mathematical multiply of normalized values
                
                # Normalize 0-255 to 0.0-1.0
                norm_bg_r, norm_bg_g, norm_bg_b = bg_r/255.0, bg_g/255.0, bg_b/255.0
                norm_fg_r, norm_fg_g, norm_fg_b = fg_r/255.0, fg_g/255.0, fg_b/255.0
                
                # Multiply
                mul_r = norm_bg_r * norm_fg_r * 255.0
                mul_g = norm_bg_g * norm_fg_g * 255.0
                mul_b = norm_bg_b * norm_fg_b * 255.0
                
                # Interpolate with Opacity
                out_r = (mul_r * self.opacity) + (bg_r * (1.0 - self.opacity))
                out_g = (mul_g * self.opacity) + (bg_g * (1.0 - self.opacity))
                out_b = (mul_b * self.opacity) + (bg_b * (1.0 - self.opacity))

            # Clamp and Convert to Integer
            out_r = min(255, max(0, int(out_r)))
            out_g = min(255, max(0, int(out_g)))
            out_b = min(255, max(0, int(out_b)))
            
            result_buffer.append((out_r, out_g, out_b))

        return result_buffer
