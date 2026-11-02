from animations.effects.base_effect import BaseEffect
from managers.errors import ValidationError
from managers.validator import integer, number, rgb


class Layer:
    def __init__(self, effect, opacity=1.0, enabled=True, blending_mode="normal", target_zones=None):
        if not isinstance(effect, BaseEffect):
            raise TypeError("Layer effect must inherit BaseEffect.")
        if type(enabled) is not bool:
            raise ValidationError("Layer enabled must be a boolean.")
        if blending_mode not in ("normal", "add", "multiply"):
            raise ValidationError("Unknown blending mode.")
        if target_zones is not None:
            if not isinstance(target_zones, (list, tuple)):
                raise ValidationError("Target zones must be a list of indices.")
            target_zones = tuple(integer(index, "Zone index", 0) for index in target_zones)
        self.effect = effect
        self.opacity = opacity
        self.enabled = enabled
        self.blending_mode = blending_mode
        self.target_zones = target_zones

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = number(value, "Opacity", 0, 1)

    def process(self, background_buffer, led_count, led_positions=None):
        if len(background_buffer) != led_count:
            raise ValidationError("Background size does not match the LED count.")
        if self.target_zones and max(self.target_zones) >= led_count:
            raise ValidationError("Target zone is outside the device layout.")
        if not self.enabled or not self.effect.enabled or self.opacity == 0:
            return list(background_buffer)
        foreground = self.effect.apply(led_count, led_positions)
        if len(foreground) != led_count:
            raise ValidationError("Effect must return one color per LED.")
        output = []
        for index in range(led_count):
            background = rgb(background_buffer[index])
            if self.target_zones is not None and index not in self.target_zones:
                output.append(background)
                continue
            color = rgb(foreground[index])
            if self.blending_mode == "normal":
                mixed = [
                    front * self.opacity + back * (1 - self.opacity)
                    for front, back in zip(color, background, strict=True)
                ]
            elif self.blending_mode == "add":
                mixed = [back + front * self.opacity for front, back in zip(color, background, strict=True)]
            else:
                mixed = [
                    back * front / 255 * self.opacity + back * (1 - self.opacity)
                    for front, back in zip(color, background, strict=True)
                ]
            output.append(tuple(min(255, max(0, int(channel))) for channel in mixed))
        return output
