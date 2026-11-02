import sys
import threading
import queue
import time
from abc import ABC, abstractmethod
from typing import List, Tuple, Any, Optional
from pathlib import Path


root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from schemas import MouseCapabilities
class BaseMouse(ABC):
    """
    Abstract Base Class for all mouse drivers in Muvv.
    This serves as the 'constitution' for any new mouse addition.
    All driver implementations MUST inherit from this class and implement
    these methods.
    """

    CAPABILITIES: MouseCapabilities = {} 
    ZONE_MAP: dict = {}

    def __init__(self, vendor_id: int, product_id: int, max_fps: int = 30, device_path: Optional[str] = None):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.max_fps = max_fps
        self.device_path = device_path
        self.is_connected = False
        self.device: Any = None
        self.lock = threading.Lock()
        
        # Async I/O Queue
        # Format: (data_bytes, post_write_delay_seconds)
        self.command_queue = queue.Queue()
        
        # Start Worker Thread
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def get_capabilities(self) -> MouseCapabilities:
        return self.CAPABILITIES

    def _worker_loop(self):
        """
        Background thread that consumes the command queue and writes to the device.
        This ensures all I/O is serialized and non-blocking for the main thread.
        """
        while True:
            try:
                packet, delay = self.command_queue.get()
                
                # Check for connection before writing
                if self.is_connected and hasattr(self, 'device') and self.device:
                    try:
                        self.device.write(packet)
                        if delay > 0:
                            time.sleep(delay)
                    except Exception as e:
                        print(f"Async Write Error: {e}")
                
                self.command_queue.task_done()
                
            except Exception as e:
                print(f"Worker Loop Error: {e}")

    @abstractmethod
    def connect(self) -> None:
        """
        Establishes connection with the physical device.
        Must handle HID device opening and initial handshake.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Safely closes the connection with the device.
        Must ensure resource cleanup.
        """
        # Wait for all pending async commands to finish
        if hasattr(self, 'command_queue'):
            self.command_queue.join()
        pass

    @abstractmethod
    def reconnect(self) -> None:
        """
        Attempts to reconnect to the device if connection is lost.
        """
        pass

    @abstractmethod
    def set_color(self, led_zone: str, color: Tuple[int, int, int]) -> None:
        """
        Sets the color of a specific LED zone in the virtual state.
        Note: This might not immediately send data to device, depending on implementation (flush usage).
        
        Args:
            led_zone: Identifier for the LED zone (e.g., "logo", "wheel").
            color: RGB tuple (r, g, b).
        """
        pass

    @abstractmethod
    def set_dpi(self, level: int) -> None:
        """
        Sets the DPI level of the mouse.
        
        Args:
            level: The DPI index or value to set.
        """
        pass

    @abstractmethod
    def save_profile(self) -> None:
        """
        Save the current configuration to the mouse's on-board memory.
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        """
        Sends the current virtual state (colors, etc.) to the physical device.
        """
        pass
