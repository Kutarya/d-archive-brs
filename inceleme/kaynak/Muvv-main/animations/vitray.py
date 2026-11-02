import time
from typing import List, Tuple
from animations.layer import Layer
from animations.maps import ZoneMap

class Vitray:
    """
    The main Animation Engine class (The Artist).
    
    It manages a stack of Layers and renders them into a final frame buffer
    based on a ZoneMap (physical layout).
    """

    def __init__(self, zone_map: ZoneMap):
        """
        Initialize the Vitray Engine.

        Args:
            zone_map: A ZoneMap instance helper describing the device layout.
        """
        self.zone_map = zone_map
        self.layers: List[Layer] = []
        self.led_count = zone_map.led_count

    def add_layer(self, layer: Layer) -> None:
        """
        Adds a new layer to the top of the stack.
        """
        self.layers.append(layer)

    def clear_layers(self) -> None:
        """
        Removes all layers.
        """
        self.layers.clear()

    def render(self) -> List[Tuple[int, int, int]]:
        """
        Renders a single frame.
        
        It starts with a black background and processes each layer
        from bottom to top.

        Returns:
            A list of (R, G, B) tuples representing the final frame.
        """
        # Start with black background
        frame_buffer = [(0, 0, 0)] * self.led_count

        # Process each layer
        for layer in self.layers:
            if layer.enabled:
                frame_buffer = layer.process(
                    background_buffer=frame_buffer,
                    led_count=self.led_count,
                    led_positions=self.zone_map.positions
                )
        
        return frame_buffer
