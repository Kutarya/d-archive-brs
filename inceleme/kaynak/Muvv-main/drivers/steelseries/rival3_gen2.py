import hid
import time
from typing import Tuple, Dict, Union, Optional
from drivers.base_mouse import BaseMouse
from animations.maps import ZoneMap
from schemas import MouseCapabilities

class Rival3Gen2Mouse(BaseMouse):
    """
    Driver for SteelSeries Rival 3 Gen 2 (Wired).
    VID: 0x1038
    PID: 0x1870
    Interface: 3
    """

    VENDOR_ID = 0x1038
    PRODUCT_ID = 0x1870
    INTERFACE_NUM = 3

    # Protocol Commands
    CMD_SET_DPI = 0x34
    CMD_SET_POLLING_RATE = 0x2B
    CMD_SAVE_MEMORY = 0x11
    CMD_SET_COLOR = 0x21
    CMD_SET_BUTTONS = 0x2A
    
    # Sub-Commands / Types
    SC_DPI_LEVELS = 0x05
    TYPE_KEYBOARD_KEY = 0x51

    # DPI / CPI Values for TrueMove Core Sensor (Source: Truemove_core.txt)
    DPI_MAP = {
        200: 0x04, 300: 0x06, 400: 0x08, 500: 0x0B, 600: 0x0D, 700: 0x0F,
        800: 0x12, 900: 0x14, 1000: 0x16, 1100: 0x19, 1200: 0x1B, 1300: 0x1D,
        1400: 0x20, 1500: 0x22, 1600: 0x24, 1700: 0x27, 1800: 0x29, 1900: 0x2B,
        2000: 0x2E, 2100: 0x30, 2200: 0x32, 2300: 0x34, 2400: 0x37, 2500: 0x39,
        2600: 0x3B, 2700: 0x3E, 2800: 0x40, 2900: 0x42, 3000: 0x45, 3100: 0x47,
        3200: 0x49, 3300: 0x4C, 3400: 0x4E, 3500: 0x50, 3600: 0x53, 3700: 0x55,
        3800: 0x57, 3900: 0x5A, 4000: 0x5C, 4100: 0x5E, 4200: 0x61, 4300: 0x63,
        4400: 0x65, 4500: 0x68, 4600: 0x6A, 4700: 0x6C, 4800: 0x6F, 4900: 0x71,
        5000: 0x73, 5100: 0x76, 5200: 0x78, 5300: 0x7A, 5400: 0x7D, 5500: 0x7F,
        5600: 0x81, 5700: 0x84, 5800: 0x86, 5900: 0x88, 6000: 0x8B, 6100: 0x8D,
        6200: 0x8F, 6300: 0x92, 6400: 0x94, 6500: 0x96, 6600: 0x99, 6700: 0x9B,
        6800: 0x9D, 6900: 0xA0, 7000: 0xA2, 7100: 0xA4, 7200: 0xA7, 7300: 0xA9,
        7400: 0xAB, 7500: 0xAD, 7600: 0xB0, 7700: 0xB2, 7800: 0xB4, 7900: 0xB7,
        8000: 0xB9, 8100: 0xBC, 8200: 0xBE, 8300: 0xC0, 8400: 0xC3, 8500: 0xC5,
    }

    # Polling Rate Map (Hz -> Hex)
    POLLING_RATE_MAP = {
        1000: 0x01,
        500:  0x02,
        250:  0x03,
        125:  0x04
    }

    # Button Mapping (Byte Offsets)
    BUTTON_MAP = {
        'button1': 1,   # Left Click
        'button2': 6,   # Right Click
        'button3': 11,  # Middle Click
        'button4': 16,  # Side Back
        'button5': 21,  # Side Forward
        'dpi':     26,  # DPI Button
        'scrollup': 31,
        'scrolldown': 36
    }



    CAPABILITIES: MouseCapabilities = {
            "dpi": {
                "type": "stages",
                "max_stages": 5,
                "supported_values": list(DPI_MAP.keys()) # Değerleri senin DPI_MAP'ten otomatik çektik
            },
            "polling_rates": list(POLLING_RATE_MAP.keys()), # [1000, 500, 250, 125]
            "rgb": {
                "supported": True,
                "zones": ["wheel", "middle", "underglow"],
                "effects": ["static", "breathing", "wave"], # Şimdilik elindeki animasyonlar
                "has_brightness": False 
            },
            "programmable_buttons": 6,
            "macro_support": True
        }
            
    ZONE_MAP = {
        'wheel': 0x01,
        'middle': 0x02,   # Middle LED
        'underglow': 0x04
    }

    def __init__(self, device_path: Optional[str] = None):
        super().__init__(self.VENDOR_ID, self.PRODUCT_ID, max_fps=30, device_path=device_path)
        self.device = None

        # Virtual LED State (Default: Off)
        # 3 Zones: wheel (0x01), middle (0x02), underglow (0x04)
        self.led_state = {
            'wheel': (0, 0, 0),
            'middle': (0, 0, 0),
            'underglow': (0, 0, 0)
        }
        
        # Physical LED Coordinates (Normalized 0.0 - 1.0)
        # Assuming Top-Left is (0,0) and Bottom-Right is (1,1)
        self.LED_COORDINATES = {
            'wheel':     (0.5, 0.1),  # Top Center
            'middle':    (0.5, 0.5),  # Middle Center (Logo Area)
            'underglow': (0.5, 0.9)   # Bottom Center
        }
        
        # Default DPI Settings (5 Levels)
        self.dpi_levels = [400, 800, 1200, 2400, 3200]
        self.active_dpi_index = 0  # 0-indexed (0 = Level 1)
        self.polling_rate = 1000   # Hz
        
        # Default Button Configuration
        self.button_config = {
            'button1': 0x01, 'button2': 0x02, 'button3': 0x03,
            'button4': 0x04, 'button5': 0x05, 'dpi': 0x30,
            'scrollup': 0x31, 'scrolldown': 0x32
        }

        # Calculate default mask (Enable all zones by default)
        self.zone_mask = 0
        for mask in self.ZONE_MAP.values():
            self.zone_mask |= mask

    def connect(self) -> None:
        """
        Establishes connection with the physical device.
        Scans for the specific VID/PID and Interface Number 3.
        """
        try:
            if self.device_path:
                self.device = hid.device()
                self.device.open_path(self.device_path)
                self.device.set_nonblocking(1)
                self.is_connected = True
                print(f"Connected to Rival 3 Gen 2 at {self.device_path}")
                return

            found = False
            for d in hid.enumerate(self.VENDOR_ID, self.PRODUCT_ID):
                if d.get('interface_number') == self.INTERFACE_NUM:
                    self.device_path = d['path']
                    found = True
                    break
            
            if not found:
                raise ConnectionError(f"Rival 3 Gen 2 (Interface {self.INTERFACE_NUM}) not found.")

            self.device = hid.device()
            self.device.open_path(self.device_path)
            self.device.set_nonblocking(1) # Asynchronous reading if needed later
            self.is_connected = True
            print(f"Connected to Rival 3 Gen 2 at {self.device_path}")

        except Exception as e:
            self.is_connected = False
            self.device = None
            raise ConnectionError(f"Failed to connect to Rival 3 Gen 2: {e}")

    def disconnect(self) -> None:
        """
        Safely closes the connection with the device.
        """
        # Ensure async queue is empty (defined in BaseMouse)
        super().disconnect()
        
        if self.device:
            try:
                self.device.close()
            except Exception as e:
                print(f"Error during disconnect: {e}")
            finally:
                self.device = None
                self.is_connected = False
                print("Disconnected from Rival 3 Gen 2")

    def reconnect(self) -> None:
        """
        Attempts to reconnect to the device if connection is lost.
        """
        self.disconnect()
        self.connect()

    def set_color(self, led_zone: str, color: Tuple[int, int, int]) -> None:
        """
        Sets the color of a specific LED zone in the virtual state.
        DOES NOT send data to device. Use flush() to apply changes.
        """
        if led_zone not in self.ZONE_MAP:
            print(f"Warning: Invalid LED zone '{led_zone}'")
            return
            
        self.led_state[led_zone] = color

    def set_dpi(self, level_index: int) -> None:
        """
        Sets the active DPI slot and updates all slot configuration.
        Note: The protocol requires sending all 5 slot values every time.
        
        Args:
            level_index: The index of the DPI level to activate (0-4).
        """
        if not (0 <= level_index < 5):
            print(f"Error: Invalid DPI index {level_index}. Must be 0-4.")
            return

        self.active_dpi_index = level_index
        
        if not self.is_connected or not self.device:
            return

        try:
            # Command 0x34: Set DPI
            # Byte 0: CMD_SET_DPI
            # Byte 1: SC_DPI_LEVELS
            # Byte 2: Active Slot Index
            # Bytes 3-12: DPI Values for 5 slots (X, Y for each)
            
            packet = bytearray(64)
            packet[0] = self.CMD_SET_DPI
            packet[1] = self.SC_DPI_LEVELS
            packet[2] = self.active_dpi_index
            
            idx = 3
            for dpi in self.dpi_levels:
                hex_val = self.DPI_MAP.get(dpi, 0x12) # Default to 800 if not found
                packet[idx] = hex_val     # X Axis
                packet[idx + 1] = hex_val # Y Axis
                idx += 2
                
            self.command_queue.put((bytes(packet), 0))
            print(f"DPI set to Level {level_index + 1} ({self.dpi_levels[level_index]} DPI)")
            
        except Exception as e:
            print(f"Error setting DPI: {e}")

    def set_dpi_stages(self, new_stages_list: list) -> None:
        """
        Updates the 5 DPI stages (levels) for the mouse.
        
        Args:
            new_stages_list: A list of exactly 5 integers (e.g., [400, 800, 1200, 2400, 3200]).
                             Values must be valid DPI steps supported by the sensor.
        """
        if not isinstance(new_stages_list, list) or len(new_stages_list) != 5:
            print("Error: DPI stages list must contain exactly 5 integers.")
            return
            
        # Validate that all DPI values are supported
        for dpi in new_stages_list:
            if dpi not in self.DPI_MAP:
                print(f"Error: Invalid DPI value {dpi}. Supported values: {list(self.DPI_MAP.keys())}")
                return

        # Update the internal state
        self.dpi_levels = new_stages_list
        print(f"DPI Stages updated to: {self.dpi_levels}")
        
        # Apply the changes to the device immediately by re-setting the active DPI
        # This triggers sending the new 5-level configuration packet.
        self.set_dpi(self.active_dpi_index)

    def set_polling_rate(self, hz: int) -> None:
        """
        Sets the polling rate of the mouse.
        Supported values: 125, 250, 500, 1000 Hz.
        """
        if hz not in self.POLLING_RATE_MAP:
            print(f"Error: Invalid polling rate {hz}Hz. Supported: {list(self.POLLING_RATE_MAP.keys())}")
            return
            
        self.polling_rate = hz
        
        if not self.is_connected or not self.device:
            return
            
        try:
            # Command 0x2B: Set Polling Rate
            packet = bytearray(64)
            packet[0] = self.CMD_SET_POLLING_RATE
            packet[1] = self.POLLING_RATE_MAP[hz]
            
            self.command_queue.put((bytes(packet), 0))
            print(f"Polling Rate set to {hz}Hz")
            
        except Exception as e:
            print(f"Error setting polling rate: {e}")

    def save_profile(self) -> None:
        """
        Saves current configuration (DPI, Polling Rate, Colors) to on-board memory.
        """
        if not self.is_connected or not self.device:
            return

        try:
            # Command 0x11: Save to Memory
            packet = bytearray(64)
            packet[0] = self.CMD_SAVE_MEMORY
            packet[1] = 0x00
            
            self.command_queue.put((bytes(packet), 0))
            print("Profile saved to on-board memory.")
            
        except Exception as e:
            print(f"Error saving profile: {e}")

    def flush(self) -> None:
        """
        Sends the current virtual state (colors) to the physical device.
        Constructs a 64-byte packet with Command 0x21.
        """
        if not self.is_connected or not self.device:
            return

        try:
            # 1. Prepare Packet (64 Bytes)
            # Byte 0: Header (CMD_SET_COLOR)
            # Byte 1: Zone Mask - Use the dynamic mask variable
            packet = bytearray(64)
            packet[0] = self.CMD_SET_COLOR
            packet[1] = self.zone_mask

            # 2. Fill Color Data
            # Protocol:
            # Bytes 2-4: Zone 1 (Wheel)
            # Bytes 5-7: Zone 2 (Middle/Logo)
            # Bytes 8-10: Zone 3 (Underglow)
            
            # Zone 1: Wheel
            r, g, b = self.led_state.get('wheel', (0,0,0))
            packet[2] = r
            packet[3] = g
            packet[4] = b

            # Zone 2: Middle
            r, g, b = self.led_state.get('middle', (0,0,0))
            packet[5] = r
            packet[6] = g
            packet[7] = b

            # Zone 3: Underglow
            r, g, b = self.led_state.get('underglow', (0,0,0))
            packet[8] = r
            packet[9] = g
            packet[10] = b

            # 3. Send Packet (Async)
            self.command_queue.put((bytes(packet), 0))
            
        except Exception as e:
            print(f"Error sending color packet: {e}")
            # Optional: Automatic reconnect logic/flag could be set here

    def set_buttons(self, mapping: dict) -> None:
        """
        Configures button assignments (Re-mapping).
        
        Args:
            mapping: Dictionary { 'button_name': value }.
                     Value can be:
                     - int: Mouse function code (e.g. 0x01 for Left Click)
                     - tuple: (Type, Code) for special keys (e.g. (0x51, 0x04) for Keyboard 'A')
        """
        if not self.is_connected or not self.device:
            return

        # Update internal state with new mapping
        self.button_config.update(mapping)

        # Prepare Packet
        # Header: CMD_SET_BUTTONS
        packet = bytearray(64)
        packet[0] = self.CMD_SET_BUTTONS
        
        has_left_click = False

        for btn, val in self.button_config.items():
            if btn not in self.BUTTON_MAP:
                continue
            
            idx = self.BUTTON_MAP[btn]
            
            # Case A: Simple Mouse Function (int)
            if isinstance(val, int):
                packet[idx] = val
                if val == 0x01: # Check for Left Click
                    has_left_click = True
            
            # Case B: Complex Key/Macro (Tuple)
            elif isinstance(val, (tuple, list)) and len(val) == 2:
                packet[idx] = val[0]   # Type (e.g. TYPE_KEYBOARD_KEY)
                packet[idx+1] = val[1] # KeyCode
                # Note: Keyboard keys are not Left Click -> has_left_click stays False for this button

        # Critical Safety Check
        if not has_left_click:
            print("CRITICAL ERROR: Configuration Rejected! You must have at least one button assigned as Left Click (0x01).")
            # We should probably revert the internal state if we reject?
            # For now, just returning without sending prevents damage.
            return

        # Send Packet and Save (Async Sequence)
        try:
            # 1. Send Button Config + Wait 0.05s
            self.command_queue.put((bytes(packet), 0.05))
            
            # 2. Save Command
            cmd_save = bytes([self.CMD_SAVE_MEMORY]) + b'\x00'*63
            self.command_queue.put((cmd_save, 0))
            
            print("Button configuration queued (Async).")
            
        except Exception as e:
            print(f"Error setting buttons: {e}")

    def bind_key(self, button: str, key_code: int) -> None:
        """
        Helper to bind a keyboard key to a mouse button.
        Uses Keyboard Mode (0x51).
        
        Args:
            button: 'button1'...'button5', etc.
            key_code: HID Key Code (e.g. 0x04 for 'A').
        """
        # Create mapping tuple (Type ID: TYPE_KEYBOARD_KEY, KeyCode)
        mapping = {button: (self.TYPE_KEYBOARD_KEY, key_code)}
        self.set_buttons(mapping)

    def get_zone_map(self) -> ZoneMap:
        """
        Returns a ZoneMap instance configured for this device.
        """
        return ZoneMap(self.LED_COORDINATES)
