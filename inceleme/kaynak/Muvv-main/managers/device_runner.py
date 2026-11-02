import threading
import time
from typing import Type, Optional
import sys
import os

# Add project root to sys.path if this file is run directly (for testing)
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from drivers.base_mouse import BaseMouse
from animations.vitray import Vitray
from animations.maps import ZoneMap

class DeviceRunner:
    """
    Manages the lifecycle of a single device (Driver + Animation Engine).
    Runs in its own thread to ensure performance isolation.
    """

    def __init__(self, driver_class: Type[BaseMouse], device_path: str = None):
        """
        Initialize the Device Runner.

        Args:
            driver_class: The class of the driver to instantiate (e.g. Rival3Gen2Mouse)
            device_path: Optional HID path if known, otherwise driver might scan again (driver dependent)
        """
        self.driver_class = driver_class
        self.device_path = device_path
        
        # Instantiate Driver
        self.driver: BaseMouse = self.driver_class(device_path=self.device_path)
        # The driver uses device_path for direct connection

        self.engine: Optional[Vitray] = None
        self.zone_map: Optional[ZoneMap] = None
        
        # Threading Control
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.is_running = False

    def start(self):
        """
        Starts the device connection and the render loop thread.
        """
        if self.is_running:
            print(f"DeviceRunner for {self.driver.product_id} is already running.")
            return

        print(f"Starting DeviceRunner for VID: {self.driver.vendor_id}, PID: {self.driver.product_id}...")

        try:
            # 1. Connect to Hardware
            self.driver.connect()
            if not self.driver.is_connected:
                print("Failed to connect to device.")
                return

            # 2. Setup Animation Engine
            # The driver knows its physical layout
            self.zone_map = self.driver.get_zone_map()
            self.engine = Vitray(self.zone_map)
            
            print(f"Vitray Engine initialized with {self.zone_map.led_count} zones.")

            # 3. Start Render Loop
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._render_loop, daemon=True)
            self._thread.start()
            self.is_running = True
            print("Render loop started.")

        except Exception as e:
            print(f"Error starting DeviceRunner: {e}")
            self.stop()

    def stop(self):
        """
        Stops the render loop and disconnects the device.
        """
        print("Stopping DeviceRunner...")
        self._stop_event.set()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        if self.driver:
            # Turn off LEDs before disconnecting
            if self.zone_map:
                try:
                    for i in range(self.zone_map.led_count):
                        zone_name = self.zone_map.get_name(i)
                        if zone_name:
                            self.driver.set_color(zone_name, (0, 0, 0))
                    self.driver.flush()
                except Exception as e:
                    print(f"Error turning off LEDs: {e}")

            self.driver.disconnect()
            
        self.is_running = False
        print("DeviceRunner stopped.")

    def _render_loop(self):
        """
        The main loop that renders frames and pushes them to the device.
        Respects the driver's max_fps.
        """
        target_fps = self.driver.max_fps
        frame_time = 1.0 / target_fps
        
        print(f"Engine running at target {target_fps} FPS")

        while not self._stop_event.is_set():
            start_time = time.time()

            try:
                # 1. Render Frame (Calculate Colors)
                # Engine is hardware agnostic, returns list of (r,g,b)
                frame_data = self.engine.render()

                # 2. Map to Device (Apply to Driver)
                # ZoneMap ensures the order of LEDs matches what the driver expects
                for i, color in enumerate(frame_data):
                    zone_name = self.zone_map.get_name(i)
                    if zone_name:
                        self.driver.set_color(zone_name, color)

                # 3. Flush to Hardware (Send USB Packet)
                self.driver.flush()

            except Exception as e:
                print(f"Error in render loop: {e}")
                # Ideally, we might want to try reconnecting here if it's a connection error
                time.sleep(1) # Prevent busy loop log spam

            # 4. FPS Limiter
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            time.sleep(sleep_time)

    def set_effect(self, effect_name: str, options: dict = None) -> bool:
        """
        Dynamically changes the active effect on the animation engine.
        """
        if not self.engine:
            return False
            
        print(f"DeviceRunner [{self.device_path}]: Setting effect to {effect_name}")
        
        # Clear existing layers to prevent compounding effects
        self.engine.layers.clear()
        
        from animations.layer import Layer
        from animations.effect_registry import get_effect_class
        
        effect_class = get_effect_class(effect_name)
        if effect_class:
            effect_instance = effect_class()
            if options:
                effect_instance.update_parameters(**options)
                
            layer = Layer(effect=effect_instance)
            self.engine.add_layer(layer)
        else:
             print(f"Unknown effect '{effect_name}' requested.")
             return False
             
        # Immediately render and flush one frame to show response instantly
        if self.zone_map and self.driver:
            pass # The render loop thread will pick this up on its next cycle.
            
        return True
        
    def set_color(self, hex_color: str) -> bool:
        """
        Dynamically changes the device to a static color using the animation engine.
        """
        if not self.engine:
            return False
            
        print(f"DeviceRunner [{self.device_path}]: Setting static color to {hex_color}")
        
        # Parse hex color (e.g., "#FF0000" or "FF0000")
        hex_color = hex_color.lstrip('#')
        try:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            print("Invalid hex color format.")
            return False

        from animations.layer import Layer
        from animations.effects.static_color import StaticColor
        
        self.engine.layers.clear()
        layer = Layer(effect=StaticColor(color=(r, g, b)))
        self.engine.add_layer(layer)
        
        return True

    def set_dpi(self, level: int) -> bool:
        """
        Sets the active DPI stage/level on the physical device driver.
        """
        if not self.driver or not self.driver.is_connected:
            print("Driver not connected.")
            return False
            
        try:
            self.driver.set_dpi(level)
            return True
        except Exception as e:
            print(f"Error setting DPI on driver: {e}")
            return False

    def set_polling(self, hz: int) -> bool:
        """
        Sets the polling rate (Hz) on the physical device driver.
        """
        if not self.driver or not self.driver.is_connected:
            print("Driver not connected.")
            return False

        if hasattr(self.driver, "set_polling_rate"):
            try:
                self.driver.set_polling_rate(hz)
                return True
            except Exception as e:
                print(f"Error setting polling rate on driver: {e}")
                return False
        else:
            print("Driver does not support setting polling rate.")
            return False

    def bind_key(self, button: str, key_code: int) -> bool:
        """
        Binds a keyboard key to a mouse button on the physical device driver.
        """
        if not self.driver or not self.driver.is_connected:
            print("Driver not connected.")
            return False

        if hasattr(self.driver, "bind_key"):
            try:
                self.driver.bind_key(button, key_code)
                return True
            except Exception as e:
                print(f"Error binding key on driver: {e}")
                return False
        else:
            print("Driver does not support key binding.")
            return False

    def save_profile(self) -> bool:
        """
        Saves current configuration to on-board memory of the physical device driver.
        """
        if not self.driver or not self.driver.is_connected:
            print("Driver not connected.")
            return False

        try:
            self.driver.save_profile()
            return True
        except Exception as e:
            print(f"Error saving profile on driver: {e}")
            return False

    def get_capabilities(self) -> dict:
        """
        Returns the hardware capabilities dictionary of the driver.
        """
        if self.driver:
            return self.driver.get_capabilities()
        return {}

