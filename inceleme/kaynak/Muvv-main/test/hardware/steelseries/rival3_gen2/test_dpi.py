import sys
import os
import time
from pathlib import Path


root_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse

def main():
    print("=== Rival 3 Gen 2 DPI Test ===\n")
    
    mouse = Rival3Gen2Mouse()
    
    try:
        print("Connecting to mouse...")
        mouse.connect()
        print("Connected successfully!\n")
        
        # Test Sequence
        input("Press Enter to set DPI to Level 1 (400 DPI) - Mouse should be very slow...")
        mouse.set_dpi(0)
        
        input("Press Enter to set DPI to Level 2 (800 DPI) - Normal speed...")
        mouse.set_dpi(1)
        
        input("Press Enter to set DPI to Level 3 (1200 DPI) - Faster...")
        mouse.set_dpi(2)
        
        input("Press Enter to set DPI to Level 4 (2400 DPI) - Very Fast...")
        mouse.set_dpi(3)
        
        input("Press Enter to set DPI to Level 5 (3200 DPI) - Extremely Fast...")
        mouse.set_dpi(4)
        
        print("\n--- Testing Polling Rate ---")
        input("Press Enter to set Polling Rate to 125Hz...")
        mouse.set_polling_rate(125)
        
        input("Press Enter to set Polling Rate to 1000Hz (Default)...")
        mouse.set_polling_rate(1000)
        
        print("\n--- Testing Save Profile ---")
        input("Press Enter to SAVE current settings to on-board memory...")
        mouse.save_profile()
        print("Saved!")
        
        print("\nTest Complete! disconnecting...")
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        mouse.disconnect()
        print("Exiting.")

if __name__ == "__main__":
    main()
