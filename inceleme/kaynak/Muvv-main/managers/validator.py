from typing import Tuple, Optional

class CommandValidator:
    """
    Validates incoming hardware commands against a device's CAPABILITIES.
    """

    @staticmethod
    def validate_dpi(capabilities: dict, level: int) -> Tuple[bool, Optional[str]]:
        """Validates if the DPI stage index is within valid range."""
        dpi_info = capabilities.get("dpi", {})
        max_stages = dpi_info.get("max_stages", 5)
        
        if not (0 <= level < max_stages):
            return False, f"Invalid DPI stage index {level}. Device supports levels 0 to {max_stages - 1}."
            
        return True, None

    @staticmethod
    def validate_polling(capabilities: dict, hz: int) -> Tuple[bool, Optional[str]]:
        """Validates if the requested polling rate is supported."""
        supported_rates = capabilities.get("polling_rates", [])
        if supported_rates and hz not in supported_rates:
            return False, f"Unsupported polling rate {hz}Hz. Supported rates: {supported_rates}"
            
        return True, None

    @staticmethod
    def validate_button(capabilities: dict, button: str) -> Tuple[bool, Optional[str]]:
        """Validates button identifier."""
        if not button or not isinstance(button, str):
            return False, "Invalid button identifier."
        return True, None
