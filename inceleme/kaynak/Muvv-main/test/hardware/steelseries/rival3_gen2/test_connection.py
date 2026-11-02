import sys
import os
import time
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse

def test_connection():
    print("=== Rival 3 Gen 2 Connection Test ===")
    mouse = Rival3Gen2Mouse()

    try:
        print("Connecting...")
        mouse.connect()
        
        if mouse.is_connected:
            print("SUCCESS: Connected to device.")
            print(f"Device Path: {mouse.device_path}")
            
            # Keep connection open for a short time
            time.sleep(1)
            
        else:
            print("FAILED: is_connected returned False.")

    except Exception as e:
        print(f"ERROR: Exception occurred during connection: {e}")
        print("\nPossible Causes:")
        print("1. Device not plugged in.")
        print("2. udev rules not set (access denied).")
        print("3. Another program is using the device.")

    finally:
        print("Disconnecting...")
        mouse.disconnect()
        print("Test completed.")

if __name__ == "__main__":
    test_connection()
