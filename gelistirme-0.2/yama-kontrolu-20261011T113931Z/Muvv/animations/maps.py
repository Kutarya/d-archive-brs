from managers.errors import ValidationError
from managers.validator import number


class ZoneMap:
    def __init__(self, zone_layout):
        if not isinstance(zone_layout, dict) or not zone_layout or len(zone_layout) > 64:
            raise ValidationError("Zone layout must contain 1–64 named zones.")
        positions = []
        for name, point in zone_layout.items():
            if not isinstance(name, str) or not name:
                raise ValidationError("LED zones require names.")
            if not isinstance(point, (tuple, list)) or len(point) != 2:
                raise ValidationError("LED coordinates must contain x and y.")
            positions.append(tuple(number(value, "Coordinate", 0, 1) for value in point))
        self.zone_names = list(zone_layout)
        self.positions = positions
        self.led_count = len(self.zone_names)
        self.name_to_index = {name: index for index, name in enumerate(self.zone_names)}

    def get_index(self, zone_name):
        return self.name_to_index.get(zone_name)

    def get_position(self, index):
        return self.positions[index] if type(index) is int and 0 <= index < self.led_count else (0.0, 0.0)

    def get_name(self, index):
        return self.zone_names[index] if type(index) is int and 0 <= index < self.led_count else None
