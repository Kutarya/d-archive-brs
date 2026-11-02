import math
import re

from managers.errors import ValidationError


def integer(value, name, minimum=None, maximum=None):
    if type(value) is not int:
        raise ValidationError(f"{name} must be an integer.")
    if minimum is not None and value < minimum:
        raise ValidationError(f"{name} must be at least {minimum}.")
    if maximum is not None and value > maximum:
        raise ValidationError(f"{name} must be at most {maximum}.")
    return value


def number(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number.")
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValidationError(f"{name} must be between {minimum} and {maximum}.")
    return float(value)


def rgb(value):
    if isinstance(value, str):
        if not re.fullmatch(r"#?[0-9a-fA-F]{6}", value):
            raise ValidationError("Color must contain exactly six hexadecimal digits.")
        value = value.removeprefix("#")
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValidationError("Color must contain three RGB channels.")
    return tuple(integer(channel, "RGB channel", 0, 255) for channel in value)


def key_code(value):
    integer(value, "Keyboard usage", 0, 255)
    # Supported subset of the HID Keyboard/Keypad usage page.
    if not (0x04 <= value <= 0xA4 or 0xE0 <= value <= 0xE7):
        raise ValidationError("Unsupported keyboard usage; use 0x04–0xA4 or 0xE0–0xE7.")
    return value


class CommandValidator:
    @staticmethod
    def validate_dpi(capabilities, level):
        try:
            integer(level, "DPI stage", 0)
            info = capabilities.get("dpi")
            if not isinstance(info, dict):
                raise ValidationError("Device does not declare DPI support.")
            if info.get("type") == "stages":
                maximum = integer(info.get("max_stages"), "Stage count", 1)
                if level >= maximum:
                    raise ValidationError(
                        f"Invalid DPI stage index {level}. Device supports levels 0 to {maximum - 1}."
                    )
            elif info.get("type") == "range":
                integer(level, "DPI", info["min"], info["max"])
                if (level - info["min"]) % info["step"]:
                    raise ValidationError("DPI does not match the device step.")
            else:
                raise ValidationError("Unsupported DPI capability.")
            return True, None
        except (ValidationError, KeyError, TypeError, ZeroDivisionError) as error:
            return False, str(error)

    @staticmethod
    def validate_polling(capabilities, hz):
        try:
            integer(hz, "Polling rate", 1)
            rates = capabilities.get("polling_rates")
            if not isinstance(rates, list) or not rates:
                raise ValidationError("Device does not declare polling rate support.")
            if hz not in rates:
                raise ValidationError(f"Unsupported polling rate {hz}Hz. Supported rates: {rates}")
            return True, None
        except ValidationError as error:
            return False, str(error)

    @staticmethod
    def validate_button(capabilities, button):
        names = capabilities.get("button_names")
        if not isinstance(button, str) or not names or button not in names:
            return False, f"Unknown button: {button!r}."
        return True, None

    @staticmethod
    def require(result):
        valid, message = result
        if not valid:
            raise ValidationError(message)
