from typing import Literal, TypedDict


class DpiStageCapability(TypedDict):
    type: Literal["stages"]
    max_stages: int
    supported_values: list[int]


class DpiRangeCapability(TypedDict):
    type: Literal["range"]
    min: int
    max: int
    step: int


class RgbCapability(TypedDict):
    supported: bool
    zones: list[str]
    effects: list[str]
    has_brightness: bool


class MouseCapabilities(TypedDict, total=False):
    dpi: DpiStageCapability | DpiRangeCapability | None
    polling_rates: list[int] | None
    rgb: RgbCapability | None
    programmable_buttons: int | None
    button_names: list[str]
    keyboard_usage_ranges: list[list[int]]
    macro_support: bool
    hardware_readback: bool
