import sys
import os
import time
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse
from animations.vitray import Vitray
from animations.maps import ZoneMap
from animations.layer import Layer
from animations.effects.static_color import StaticColor

def test_vitray_engine():
    print("=== Vitray Engine Full Pipeline Test ===")
    
    # 1. Setup Hardware
    mouse = Rival3Gen2Mouse()
    zones = ['wheel', 'middle', 'underglow'] # Rival 3 specific zones
    led_count = len(zones)

    try:
        mouse.connect()
        print(f"Connected to mouse at {mouse.device_path}")
        
        # 2. Setup Vitray Engine
        # zone_map = ZoneMap(led_count=led_count) -> OLD
        zone_map = mouse.get_zone_map() # -> NEW (Driver knows the map)
        engine = Vitray(zone_map)
        
        # Helper to push frame to device
        def render_frame():
            start_time = time.time()
            
            frame = engine.render()
            for i, color in enumerate(frame):
                if i < len(zones):
                    mouse.set_color(zones[i], color)
            mouse.flush()
            
            # FPS Limiter (Target: 30 FPS)
            target_frame_time = 1.0 / 30.0
            elapsed = time.time() - start_time
            sleep_time = max(0, target_frame_time - elapsed)
            time.sleep(sleep_time)

        # 3. Create Effects & Layers
        base_effect = StaticColor(color=(255, 0, 0), name="Base Red") # Red Background
        top_effect = StaticColor(color=(0, 0, 255), name="Top Blue")  # Blue Overlay
        
        base_layer = Layer(base_effect)
        top_layer = Layer(top_effect, opacity=0.0, blending_mode='normal') # Start invisible

        # 4. Add Layers to Engine
        engine.add_layer(base_layer)
        engine.add_layer(top_layer)

        print("\n--- Phase 1: Base Layer Only (Red) ---")
        for _ in range(30 * 2): # Run for 2 seconds (30 FPS * 2)
            render_frame()

        print("\n--- Phase 2: Fade In Blue Layer (0% -> 100%) ---")
        steps = 60 # 2 seconds at 30 FPS
        for i in range(steps + 1):
            opacity = i / steps
            top_layer.opacity = opacity
            render_frame()
        
        print("\n--- Phase 3: Additive Green Layer ---")
        add_effect = StaticColor((0, 255, 0), name="Add Green")
        add_layer = Layer(add_effect, blending_mode='add', opacity=0.0)
        engine.add_layer(add_layer)
        
        # Flash Green
        for _ in range(5):
            # Flash On (0.2s = 6 frames)
            add_layer.opacity = 1.0
            for _ in range(6): render_frame()
            
            # Flash Off (0.2s = 6 frames)
            add_layer.opacity = 0.0
            for _ in range(6): render_frame()

        print("\n--- Phase 4: Breathing Effect (Purple) ---")
        from animations.effects.breathing import Breathing
        
        engine.clear_layers()
        breath_effect = Breathing(color=(255, 0, 255), speed=2.0) # Purple, Fast
        breath_layer = Layer(breath_effect)
        engine.add_layer(breath_layer)
        
        # Run for 5 seconds
        for _ in range(30 * 5):
            render_frame()

        print("\n--- Phase 5: Zone Filtering (Breathing Wheel + Static Others) ---")
        engine.clear_layers()
        
        # 1. Background (Static Red on Middle & Underglow)
        bg_zones = [
            zone_map.get_index('middle'), 
            zone_map.get_index('underglow')
        ]
        bg_effect = StaticColor(color=(255, 0, 0)) # Red
        bg_layer = Layer(bg_effect, target_zones=bg_zones)
        engine.add_layer(bg_layer)
        
        # 2. Foreground (Breathing Blue on Wheel)
        fg_zones = [zone_map.get_index('wheel')]
        fg_effect = Breathing(color=(0, 0, 255), speed=3.0) # Fast Blue Breathing
        fg_layer = Layer(fg_effect, target_zones=fg_zones)
        engine.add_layer(fg_layer)
        
        # Run
        for _ in range(30 * 5):
            render_frame()

        print("\n--- Phase 6: Vertical Wave Effect (Green) ---")
        from animations.effects.wave import Wave
        
        engine.clear_layers()
        # Vertical Wave: Should move from Top (Wheel) to Bottom (Underglow)
        wave_effect = Wave(color=(0, 255, 0), direction='vertical', speed=0.5, wave_length=1.5)
        wave_layer = Layer(wave_effect)
        engine.add_layer(wave_layer)
        
        # Run for 5 seconds
        for _ in range(30 * 5):
            render_frame()

        print("\n--- Phase 7: Dynamic Speed Up (Green Wave) ---")
        # Start Slow
        wave_effect.update_parameters(speed=0.5, color=(0, 255, 0))
        print("Speed: 0.5x")
        for _ in range(30 * 2): render_frame()

        # Speed Up
        wave_effect.update_parameters(speed=2.0, color=(255, 255, 0)) # Yellow, Fast
        print("Speed: 2.0x (Yellow)")
        for _ in range(30 * 2): render_frame()

        # Super Fast
        wave_effect.update_parameters(speed=5.0, color=(255, 0, 0)) # Red, Super Fast
        print("Speed: 5.0x (Red)")
        for _ in range(30 * 2): render_frame()

        print("\nTurning off...")
        engine.clear_layers()
        render_frame()
        print("Clean exit.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        mouse.disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    test_vitray_engine()
