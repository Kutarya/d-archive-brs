# schemas.py
from typing import TypedDict, List, Dict, Union, Literal, Optional

# Mouse 

# --- 1. DPI STANDARTLARI ---
class DpiStageCapability(TypedDict):
    type: Literal["stages"]
    max_stages: int
    supported_values: List[int] # Hangi değerlerin seçilebileceği (Senin DPI_MAP)

class DpiRangeCapability(TypedDict):
    type: Literal["range"]
    min: int
    max: int
    step: int # Atıyorum sadece 50'şer 50'şer artıyordur

# --- 2. RGB STANDARTLARI ---
class RgbCapability(TypedDict):
    supported: bool
    zones: List[str] # ['wheel', 'logo', 'underglow'] vb.
    effects: List[str] # ['static', 'breathing', 'wave'] vb.
    has_brightness: bool # Parlaklık ayarı var mı?

# --- 3. ANA CİHAZ YETENEK KARTI (KİMLİK) ---
class MouseCapabilities(TypedDict):
    # Bir cihazda bunlar ya vardır, ya da None'dır (yoktur)
    dpi: Optional[Union[DpiStageCapability, DpiRangeCapability]]
    polling_rates: Optional[List[int]] # [125, 250, 500, 1000]
    rgb: Optional[RgbCapability]
    programmable_buttons: Optional[int] # Örn: 6 (Toplam programlanabilir tuş sayısı)
    macro_support: bool # Makro kaydedebiliyor mu?