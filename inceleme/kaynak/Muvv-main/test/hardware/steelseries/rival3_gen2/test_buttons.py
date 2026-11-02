import sys
import os
import time
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))
    
from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse

def main():
    print("=== Rival 3 Gen 2 Button Mapping Test ===\n")
    
    mouse = Rival3Gen2Mouse()
    
    try:
        print("Connecting to mouse...")
        mouse.connect()
        print("Connected successfully!\n")
        
        # Test 1: Bind Button 5 to 'A'
        print("\n--- Test 1: Binding Button 5 (Side Forward) to Key 'A' ---")
        input("Press Enter to apply binding...")
        
        # Key Code 0x04 is 'A' in HID
        mouse.bind_key('button5', 0x04)
        print("Binding applied!")
        print("Please open a text editor or click here, then press the 'Side Forward' button on your mouse.")
        print("It should type 'a'.")
        
        input("\nPress Enter when verify is done to REVERT changes...")
        
        # Test 2: Revert to Default
        print("\n--- Test 2: Reverting Button 5 to Default (Forward) ---")
        # Default for button5 is 0x05 (Forward)
        # We use set_buttons to map it back to a standard mouse button code
        
        mouse.set_buttons({'button5': 0x05})
        print("Reverted to default 'Forward' function.")
        print("Try pressing the button in a browser (should go forward history) or check if it stopped typing 'a'.")
        
        input("\nPress Enter to Finish...")
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        mouse.disconnect()
        print("Exiting.")

if __name__ == "__main__":
    main()
