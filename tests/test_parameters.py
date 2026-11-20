"""Demo-only parameter editor tests."""
import unittest
from obd_ai.parameters import DemoParameterStore, DEFINITIONS, ParameterError


class ParameterStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = DemoParameterStore()

    def test_all_parameters_have_valid_defaults(self):
        for key, definition in DEFINITIONS.items():
            self.assertLessEqual(definition.minimum, definition.default)
            self.assertLessEqual(definition.default, definition.maximum)
            self.assertEqual(self.store.read(key)["mode"], "demo")

    def test_preview_does_not_change_value(self):
        current = self.store.read("idle_target")["value"]
        result = self.store.preview("idle_target", 800)
        self.assertEqual(result["previous"], current)
        self.assertEqual(result["proposed"], 800)
        self.assertEqual(self.store.read("idle_target")["value"], current)

    def test_change_requires_confirmation(self):
        with self.assertRaises(ParameterError):
            self.store.apply("idle_target", 800, confirmed=False)
        self.assertEqual(self.store.read("idle_target")["value"], 750)

    def test_apply_readback_and_reset(self):
        result = self.store.apply("idle_target", 825, confirmed=True)
        self.assertEqual(result["status"], "simulated_applied")
        self.assertTrue(result["verified"])
        self.assertEqual(self.store.read("idle_target")["value"], 825)
        self.store.reset()
        self.assertEqual(self.store.read("idle_target")["value"], 750)

    def test_invalid_values_are_blocked(self):
        for key, value in (("idle_target", 400), ("fan_trigger", 120),
                           ("speed_warning", 10), ("idle_target", True),
                           ("idle_target", 805.5), ("UNSUPPORTED_WRITE", 800)):
            with self.subTest(key=key, value=value), self.assertRaises(ParameterError):
                self.store.preview(key, value)


if __name__ == "__main__":
    unittest.main()
