import os
import importlib
import inspect
from pathlib import Path
from typing import Type, Dict, Optional

# Using absolute import relative to the project root
from animations.effects.base_effect import BaseEffect

# Global registry to store discovered effect classes
# Key: effect name (lowercase), Value: Effect Class
_EFFECTS: Dict[str, Type[BaseEffect]] = {}

def load_effects():
    """
    Dynamically discovers and loads all effect subclasses from the 'effects' directory.
    This method scans the directory, imports modules, and registers classes that
    inherit from BaseEffect.
    """
    global _EFFECTS
    _EFFECTS.clear()
    
    # Resolve the absolute path to the 'effects' directory
    current_dir = Path(__file__).resolve().parent
    effects_dir = current_dir / 'effects'
    
    if not effects_dir.exists():
        print(f"Warning: Effects directory not found at {effects_dir}")
        return

    # Iterate through all files in the effects directory
    for filename in os.listdir(effects_dir):
        # Only process Python files and skip internal/private files
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            try:
                # Construct the module path dynamically.
                # Assumes 'animations' is available in the Python path.
                full_module_name = f"animations.effects.{module_name}"
                
                # Import the module dynamically
                module = importlib.import_module(full_module_name)
                
                # Inspect the module for classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Register classes that inherit from BaseEffect (excluding BaseEffect itself)
                    if issubclass(obj, BaseEffect) and obj is not BaseEffect:
                        effect_key = name.lower()
                        _EFFECTS[effect_key] = obj
                        
                        # Also register a shorthand name (e.g., 'WaveEffect' becomes 'wave')
                        if effect_key.endswith('effect'):
                            _EFFECTS[effect_key[:-6]] = obj
                            
            except Exception as e:
                print(f"Error loading effect module {module_name}: {e}")

def get_effect_class(effect_name: str) -> Optional[Type[BaseEffect]]:
    """
    Retrieves a specific effect class from the registry by its name.
    
    Args:
        effect_name: The name of the effect to find (case-insensitive).
        
    Returns:
        The Effect Class if found, otherwise None.
    """
    # Ensure effects are loaded before searching
    if not _EFFECTS:
        load_effects()
        
    return _EFFECTS.get(effect_name.lower())

# Automatically trigger discovery when the module is imported
load_effects()