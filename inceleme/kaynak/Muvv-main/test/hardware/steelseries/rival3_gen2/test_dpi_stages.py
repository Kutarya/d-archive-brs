import sys
import os
import time
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse

def main():
    print("=== Rival 3 Gen 2 DPI Stages Verification ===\n")
    
    mouse = Rival3Gen2Mouse()
    
    try:
        print("Connecting to mouse...")
        mouse.connect()
        print("Connected successfully!\n")
        
        print(f"Current internal DPI levels: {mouse.dpi_levels}")
        
        # Test 1: Set Custom DPI Stages
        print("\n--- Test 1: Setting Custom DPI Stages ---")
        custom_stages = [500, 1000, 1500, 2000, 2500]
        print(f"New Stages to apply: {custom_stages}")
        
        input("Press Enter to apply new stages...")
        
        mouse.set_dpi_stages(custom_stages)
        print("Custom stages applied!")
        print(f"Updated internal DPI levels: {mouse.dpi_levels}")
        print("Please press the DPI button on your mouse. You should feel the new sensitivity steps (500-2500 range).")
        
        input("\nPress Enter when verify is done to REVERT changes...")
        
        # Test 2: Revert to Default
        print("\n--- Test 2: Reverting to Default DPI Stages ---")
        default_stages = [400, 800, 1200, 2400, 3200]
        
        mouse.set_dpi_stages(default_stages)
        print("Reverted to default stages.")
        print(f"Current internal DPI levels: {mouse.dpi_levels}")
        
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
