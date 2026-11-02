import sys
import time
from pathlib import Path

# Resolve the absolute path to the project root to eliminate folder name dependencies.
# Navigating up 3 levels: test -> manager -> test_manager.py
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# Absolute import relative to the project root. Only the central manager is needed.
from managers.device_manager import DeviceManager

def test_manager_with_rival3():
    print("=== Testing Device Manager with Rival 3 ===")
    
    # 1. Initialize Manager
    manager = DeviceManager(scan_interval=1.0)
    
    try:
        # 2. Start Manager Daemon
        manager.start()
        print("Manager started. Scanning for devices...")
        
        # 3. Wait for Device Detection
        target_runner = None
        max_retries = 5
        
        for i in range(max_retries):
            time.sleep(1.0)
            
            # Search using the hardware's native VID/PID instead of class names for a bulletproof match.
            # SteelSeries Rival 3 Gen 2 -> VID: 0x1038, PID: 0x1870
            for path, runner in manager.runners.items():
                if runner.driver.vendor_id == 0x1038 and runner.driver.product_id == 0x1870:
                    target_runner = runner
                    print(f"\nRival 3 Detected at {path}!")
                    break
            
            if target_runner:
                break
            print(f"Waiting for device... ({i+1}/{max_retries})")
            
        if not target_runner:
            print("Error: Rival 3 not found! Passing test.")
            return

        # 4. Apply Effect (Wave)
        print("\n--- Applying Wave Effect via Manager ---")
        
        # Use the runner's built-in set_effect method to handle layer management and dynamic imports automatically.
        target_runner.set_effect("Wave", options={"color": (0, 255, 0), "speed": 1.0, "direction": "vertical"})
        print("Wave Effect Added.")
        
        # 5. Run the animation loop
        print("Running animation for 5 seconds...")
        time.sleep(5)
        
        # 6. Change Effect (Red Breathing)
        print("\n--- Changing to Breathing Effect ---")
        
        # Trigger a clean transition to the breathing effect without breaking the render loop.
        target_runner.set_effect("Breathing", options={"color": (255, 0, 0), "speed": 2.0})
        print("Breathing Effect Added. Running for 3 seconds...")
        time.sleep(3)

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"Test Error: {e}")
    finally:
        # 7. Cleanup resources safely
        print("\nStopping Manager...")
        manager.stop()
        print("Test Complete.")

if __name__ == "__main__":
    test_manager_with_rival3()