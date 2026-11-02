"""USB HID keyboard usage names for the desktop picker; no OS key injection."""

KEY_NAMES = {chr(65 + index): 0x04 + index for index in range(26)}
KEY_NAMES.update({str(index): 0x1D + index for index in range(1, 10)})
KEY_NAMES.update(
    {
        "0": 0x27,
        "Enter": 0x28,
        "Escape": 0x29,
        "Backspace": 0x2A,
        "Tab": 0x2B,
        "Space": 0x2C,
        "Caps Lock": 0x39,
    }
)
KEY_NAMES.update({f"F{index}": 0x39 + index for index in range(1, 13)})
KEY_NAMES.update(
    {
        "Insert": 0x49,
        "Home": 0x4A,
        "Page Up": 0x4B,
        "Delete": 0x4C,
        "End": 0x4D,
        "Page Down": 0x4E,
        "Right": 0x4F,
        "Left": 0x50,
        "Down": 0x51,
        "Up": 0x52,
        "Left Ctrl": 0xE0,
        "Left Shift": 0xE1,
        "Left Alt": 0xE2,
        "Left Super": 0xE3,
        "Right Ctrl": 0xE4,
        "Right Shift": 0xE5,
        "Right Alt": 0xE6,
        "Right Super": 0xE7,
    }
)
FUNCTION_NAMES = {
    "Sol tık": 1,
    "Sağ tık": 2,
    "Orta tık": 3,
    "Geri": 4,
    "İleri": 5,
    "DPI değiştir": 0x30,
    "Yukarı kaydır": 0x31,
    "Aşağı kaydır": 0x32,
    "Devre dışı": 0,
}


def key_label(usage):
    return next((label for label, value in KEY_NAMES.items() if value == usage), f"0x{usage:02X}")
