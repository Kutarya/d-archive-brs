import math
import unittest
from unittest.mock import patch

from support import FakeRival

from animations.effect_registry import create_effect, list_effects
from animations.effects.wave import Wave
from animations.layer import Layer
from animations.maps import ZoneMap
from animations.vitray import Vitray
from managers.device_runner import DeviceRunner
from managers.errors import TransportError, ValidationError
from managers.validator import CommandValidator, rgb


class EffectTests(unittest.TestCase):
    def test_static_aliases_and_spectrum_have_valid_default_frames(self):
        for name in ("static", "staticcolor", "breathing", "wave", "spectrum", "spectrumcycle"):
            with self.subTest(name=name):
                colors = create_effect(name).apply(3, [(0.5, 0.1), (0.5, 0.5), (0.5, 0.9)])
                self.assertEqual(len(colors), 3)
                self.assertTrue(
                    all(type(channel) is int and 0 <= channel <= 255 for color in colors for channel in color)
                )
        self.assertEqual(len(list_effects()), 4)

    def test_unknown_or_unsafe_parameters_leave_effect_unchanged(self):
        effect = Wave()
        before = effect.parameters()
        for options in (
            {"wave_length": 0},
            {"speed": math.nan},
            {"speed": math.inf},
            {"speed": True},
            {"apply": "bad"},
            {"_start_time": 1},
            {"direction": "diagonal"},
            {"color": [999, 0, 0]},
        ):
            with self.subTest(options=options), self.assertRaises(ValidationError):
                effect.update_parameters(**options)
            self.assertEqual(effect.parameters(), before)
        self.assertTrue(callable(effect.apply))

    def test_speed_is_applied_once_and_live_update_keeps_phase(self):
        with patch("animations.effects.base_effect.time.monotonic", return_value=10) as clock:
            effect = Wave(speed=2, wave_length=1)
            clock.return_value = 10.125
            self.assertEqual(effect.apply(1, [(0, 0)])[0], (255, 0, 0))
            phase = effect.get_time()
            effect.update_parameters(speed=4)
            self.assertEqual(effect.get_time(), phase)
            clock.return_value = 10.25
            self.assertAlmostEqual(effect.get_time(), 0.75)

    def test_color_formats_are_exact(self):
        self.assertEqual(rgb("#ff0080"), (255, 0, 128))
        for value in ("FFFFF", "FF0000junk", "##FF0000", [True, 0, 0], [1.5, 0, 0], [0, -1, 0]):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                rgb(value)

    def test_missing_capabilities_and_coerced_numbers_fail_closed(self):
        for capabilities in ({}, {"dpi": None, "polling_rates": None}):
            self.assertFalse(CommandValidator.validate_dpi(capabilities, 0)[0])
            self.assertFalse(CommandValidator.validate_polling(capabilities, 500)[0])
        for value in (True, 1.5, "2"):
            self.assertFalse(
                CommandValidator.validate_dpi({"dpi": {"type": "stages", "max_stages": 5}}, value)[0]
            )

    def test_blending_and_zone_selection(self):
        engine = Vitray(ZoneMap({"wheel": (0, 0), "middle": (0, 1)}))
        engine.add_layer(Layer(create_effect("static", {"color": [100, 0, 0]})))
        engine.add_layer(
            Layer(create_effect("static", {"color": [0, 100, 0]}), opacity=0.5, target_zones=[0])
        )
        self.assertEqual(engine.render(), [(50, 50, 0), (100, 0, 0)])


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.runner = DeviceRunner(FakeRival, device_path=b"test")
        self.runner.start()
        self.handle = self.runner.driver.device

    def tearDown(self):
        self.runner.stop()

    def test_start_and_stop_do_not_overwrite_current_lighting(self):
        self.assertEqual(self.handle.packets, [])
        self.runner.stop()
        self.assertEqual(self.handle.packets, [])
        self.assertTrue(self.handle.closed)

    def test_invalid_effect_preserves_existing_layer(self):
        self.runner.set_color("FF0000")
        previous = self.runner.engine.layers[0]
        for name, options in (("missing", {}), ("wave", {"wave_length": 0}), ("static", {"apply": "bad"})):
            with self.subTest(name=name), self.assertRaises(ValidationError):
                self.runner.set_effect(name, options)
            self.assertIs(self.runner.engine.layers[0], previous)

    def test_usb_failure_is_reported_and_old_effect_is_retained(self):
        self.runner.set_color("FF0000")
        previous = self.runner.engine.layers[0]
        self.handle.result = 0
        with self.assertRaises(TransportError):
            self.runner.set_color("00FF00")
        self.assertIs(self.runner.engine.layers[0], previous)

    def test_profile_tracks_unknown_fields_instead_of_fabricating_a_backup(self):
        self.runner.set_color("123456")
        profile = self.runner.host_profile("Work")
        self.assertNotIn("dpi", profile["settings"])
        self.assertIn("dpi", profile["unknown_fields"])
        self.assertFalse(profile["readback_verified"])

    def test_live_update_keeps_effect_instance_and_validates_before_changes(self):
        self.runner.set_effect("wave")
        effect = self.runner.engine.layers[0].effect
        self.runner.update_effect({"color": "00FF00", "speed": 2})
        self.assertIs(self.runner.engine.layers[0].effect, effect)
        self.assertEqual(effect.color, (0, 255, 0))
        with self.assertRaises(ValidationError):
            self.runner.update_effect({"wave_length": 0})
        self.assertEqual(effect.color, (0, 255, 0))
