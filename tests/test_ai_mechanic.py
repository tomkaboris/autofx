"""Tests for AutoFX read-only AI context and offline mode."""
import os
import unittest
from unittest.mock import patch

from obd_ai.ai_mechanic import answer, diagnostic_context


class DiagnosticAIUnitTests(unittest.TestCase):
    def test_context_allowlist_prevents_private_extra_fields(self):
        sample = {
            "mode": "demo",
            "timestamp": "2026-11-20T00:00:00+00:00",
            "sensors": {"RPM": 750, "COOLANT_TEMP": 89, "VIN": "SECRET"},
            "units": {"RPM": "rpm", "VIN": "identifier"},
            "vin": "SECRET",
            "port": "/dev/rfcomm0",
        }
        context = diagnostic_context(sample, [{"code": "P0300", "description": "Test"}])
        serialized = str(context)
        self.assertNotIn("SECRET", serialized)
        self.assertNotIn("/dev/rfcomm0", serialized)
        self.assertEqual(context["sensors"]["RPM"], 750)
        self.assertEqual(context["mode"], "demo")

    def test_offline_demo_is_clearly_labeled(self):
        snapshot = diagnostic_context(
            {"mode": "demo", "sensors": {"RPM": 800}, "units": {}},
            [{"code": "P0300", "description": "Demo"}],
        )
        result = answer("Check misfire", snapshot, "offline")
        self.assertIn("DEMO", result)
        self.assertIn("P0300", result)
        self.assertIn("bez AI modela", result)

    def test_missing_key_does_not_attempt_cloud_request(self):
        snapshot = diagnostic_context({}, [])
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
                answer("Check data", snapshot, "openai")

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            answer("test", diagnostic_context({}, []), "unsupported")


if __name__ == "__main__":
    unittest.main()
