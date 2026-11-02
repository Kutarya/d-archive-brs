from typing import List, Tuple, Dict, Optional

class ZoneMap:
    """
    Represents the physical layout of LEDs on a device.
    
    It maps logical zones (e.g., 'wheel') to indices and holds
    normalized (x, y) coordinates (0.0 - 1.0) for spatial effects.
    """

    def __init__(self, zone_layout: Dict[str, Tuple[float, float]]):
        """
        Initialize the ZoneMap with a layout dictionary.
        
        Args:
            zone_layout: A dictionary mapping zone names to (x, y) coordinates.
                         Order matters! It defines the index of the LED for the engine.
                         Example: 
                         {
                             'wheel': (0.5, 0.1),
                             'logo': (0.5, 0.8),
                             'underglow_left': (0.0, 0.9)
                         }
        """
        
        # Extract ordered lists from the dictionary (Python 3.7+ preserves insertion order)
        self.zone_names: List[str] = list(zone_layout.keys())
        self.positions: List[Tuple[float, float]] = list(zone_layout.values())
        
        self.led_count: int = len(self.zone_names)
        
        # Fast lookup for name -> index
        self.name_to_index: Dict[str, int] = {name: i for i, name in enumerate(self.zone_names)}

    def get_index(self, zone_name: str) -> Optional[int]:
        """
        Returns the index of a zone by name.
        """
        return self.name_to_index.get(zone_name)
    
    def get_position(self, index: int) -> Tuple[float, float]:
        """
        Returns (x, y) for a given index.
        """
        if 0 <= index < self.led_count:
            return self.positions[index]
        return (0.0, 0.0) # Default fallback

    def get_name(self, index: int) -> Optional[str]:
        """
        Returns the name of a zone by index.
        """
        if 0 <= index < self.led_count:
            return self.zone_names[index]
        return None
