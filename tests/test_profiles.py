"""Read-only profile allowlist tests. No demo backend."""
import unittest
from obd_ai.ai_mechanic import diagnostic_context, answer
from obd_ai.profiles import PROFILES, get_profile, profile_for_question


class ProfileTests(unittest.TestCase):
    def test_keys(self):
        for key in ("engine", "egr", "dpf", "scr"):
            self.assertEqual(get_profile(key).key, key)
        with self.assertRaises(ValueError):
            get_profile("CLEAR_DTC")

    def test_allowlisted_reads_only(self):
        all_commands = {name for p in PROFILES.values() for name in p.commands}
        self.assertNotIn("CLEAR_DTC", all_commands)
        self.assertNotIn("RAW_CAN", all_commands)

    def test_question_suggests_not_executes(self):
        self.assertEqual(profile_for_question("EGR ventil"), "egr")
        self.assertEqual(profile_for_question("AdBlue SCR"), "scr")
        self.assertEqual(profile_for_question("DPF filter"), "dpf")
        self.assertEqual(profile_for_question("RPM"), "engine")

    def test_profile_data_is_allowlisted(self):
        scan = {"profile": "egr", "mode": "vehicle",
                "readings": {
                    "RPM": {"value": 960, "unit": "rpm", "status": "ok"},
                    "SECRET": {"value": 1, "unit": "x", "status": "ok"},
                }}
        context = diagnostic_context({"mode": "vehicle", "sensors": {"RPM": 960}, "units": {}}, [], scan)
        self.assertEqual(context["targeted_scan"]["profile"], "egr")
        self.assertNotIn("SECRET", str(context))
        self.assertIn("EGR", answer("EGR?", context, "offline"))


if __name__ == "__main__":
    unittest.main()
