"""Unit tests for real-vehicle AI context and cloud key checks."""
import os
import unittest
from unittest.mock import patch
from obd_ai.ai_mechanic import answer, diagnostic_context


class AIContextTests(unittest.TestCase):
    def test_private_fields_never_reach_provider(self):
        reading = {
            "mode": "vehicle", "timestamp": "2026-11-20T11:00:00+00:00",
            "sensors": {"RPM": 950, "VIN": "PRIVATE"}, "units": {"RPM": "rpm"},
            "port": "PRIVATE_DEVICE",
        }
        context = diagnostic_context(reading, [{"code": "P0300", "description": "misfire"}])
        self.assertEqual(context["mode"], "vehicle")
        self.assertEqual(context["sensors"]["RPM"], 950)
        self.assertNotIn("PRIVATE", str(context))

    def test_missing_readings_are_unknown_not_fabricated(self):
        context = diagnostic_context({}, [])
        self.assertEqual(context["mode"], "unknown")
        self.assertIsNone(context["sensors"]["RPM"])
        self.assertIn("Nisu dostupna", answer("Analiziraj", context, "offline"))

    def test_no_key_disallows_cloud(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
                answer("Diagnose", diagnostic_context({}, []), "openai")

    def test_unsupported_provider(self):
        with self.assertRaises(ValueError):
            answer("Diagnose", diagnostic_context({}, []), "unsupported")


if __name__ == "__main__":
    unittest.main()
