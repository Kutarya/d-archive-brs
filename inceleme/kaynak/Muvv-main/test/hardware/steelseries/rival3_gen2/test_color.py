import sys
import os
import time
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse

def test_rgb():
    print("=== Rival 3 Gen 2 RGB Test ===")
    mouse = Rival3Gen2Mouse()

    try:
        print("Connecting...")
        mouse.connect()
        
        if not mouse.is_connected:
            print("FAILED: Could not establish connection.")
            return

        print("Connected. Starting Color Cycle...")
        
        zones = ['wheel', 'middle', 'underglow']
        
        # 1. Color all zones sequentially
        colors = [
            ("RED", (255, 0, 0)),
            ("GREEN", (0, 255, 0)),
            ("BLUE", (0, 0, 255)),
            ("WHITE", (255, 255, 255)),
            ("OFF", (0, 0, 0))
        ]

        for name, rgb in colors:
            print(f"All zones -> {name} {rgb}")
            for zone in zones:
                mouse.set_color(zone, rgb)
            
            mouse.flush()
            time.sleep(1.0)

        # 2. Zone-Based Test
        print("\nStarting Zone-Based Test...")
        
        # Wheel Only RED
        print("Wheel Only -> RED")
        mouse.set_color('wheel', (255, 0, 0))
        mouse.set_color('middle', (0, 0, 0))
        mouse.set_color('underglow', (0, 0, 0))
        mouse.flush()
        time.sleep(1.0)

        # Middle Only GREEN
        print("Middle Only -> GREEN")
        mouse.set_color('wheel', (0, 0, 0))
        mouse.set_color('middle', (0, 255, 0))
        mouse.set_color('underglow', (0, 0, 0))
        mouse.flush()
        time.sleep(1.0)

        # Underglow Only BLUE
        print("Underglow Only -> BLUE")
        mouse.set_color('wheel', (0, 0, 0))
        mouse.set_color('middle', (0, 0, 0))
        mouse.set_color('underglow', (0, 0, 255))
        mouse.flush()
        time.sleep(1.0)

        print("\nTest Completed. Turning off lights.")
        for zone in zones:
            mouse.set_color(zone, (0, 0, 0))
        mouse.flush()

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        mouse.disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    test_rgb()
