import threading
from copy import deepcopy

from animations.effects.base_effect import BaseEffect
from animations.effects.breathing import Breathing
from animations.effects.spectrum_cycle import SpectrumCycle
from animations.effects.static_color import StaticColor
from animations.effects.wave import Wave
from managers.errors import ValidationError

_EFFECTS = {}
_LOCK = threading.RLock()


def register_effect(effect_class, aliases=()):
    if not isinstance(effect_class, type) or not issubclass(effect_class, BaseEffect):
        raise TypeError("Effects must inherit BaseEffect.")
    names = [effect_class.EFFECT_ID, effect_class.__name__.lower(), *aliases]
    with _LOCK:
        for name in names:
            if name in _EFFECTS and _EFFECTS[name] is not effect_class:
                raise ValueError(f"Duplicate effect name: {name}")
        _EFFECTS.update({name: effect_class for name in names})


def load_effects():
    with _LOCK:
        _EFFECTS.clear()
        for effect_class in (StaticColor, Breathing, Wave, SpectrumCycle):
            register_effect(effect_class)


def get_effect_class(effect_name):
    if not isinstance(effect_name, str):
        return None
    with _LOCK:
        return _EFFECTS.get(effect_name.lower())


def create_effect(effect_name, options=None):
    effect_class = get_effect_class(effect_name)
    if effect_class is None:
        raise ValidationError(f"Unknown effect: {effect_name!r}.")
    instance = effect_class()
    instance.update_parameters(**effect_class.validate_parameters(options or {}))
    return instance


def list_effects():
    with _LOCK:
        classes = {cls.EFFECT_ID: cls for cls in _EFFECTS.values()}
    return [
        {"id": name, "name": cls().name, "parameters": deepcopy(cls.PARAMS), "defaults": cls().parameters()}
        for name, cls in sorted(classes.items())
    ]


load_effects()
