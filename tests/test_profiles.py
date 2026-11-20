"""Tests for profile selection, demo scans and AI privacy."""
import unittest

from obd_ai.profiles import PROFILES, demo_scan, get_profile, profile_for_question
from obd_ai.ai_mechanic import diagnostic_context, answer


class ReadOnlyProfilesTests(unittest.TestCase):
    def test_known_profiles_only(self):
        for key in ("engine", "egr", "dpf", "scr"):
            self.assertEqual(get_profile(key).key, key)
        with self.assertRaises(ValueError):
            get_profile("CLEAR_DTC")

    def test_all_commands_are_from_allowlist(self):
        names = {name for profile in PROFILES.values() for name in profile.commands}
        self.assertNotIn("CLEAR_DTC", names)
        self.assertNotIn("ATZ", names)
        self.assertNotIn("RAW_CAN", names)

    def test_question_suggestion_never_runs_scan(self):
        self.assertEqual(profile_for_question("EGR ventil ne radi"), "egr")
        self.assertEqual(profile_for_question("AdBlue SCR greška"), "scr")
        self.assertEqual(profile_for_question("DPF regeneracija"), "dpf")
        self.assertEqual(profile_for_question("Čudni obrtaji"), "engine")

    def test_demo_is_explicitly_simulated(self):
        for key in PROFILES:
            scan = demo_scan(key)
            self.assertEqual(scan["mode"], "demo")
            self.assertTrue(all(value["status"] == "simulated" for value in scan["readings"].values()))

    def test_targeted_context_filters_unknown_data(self):
        scan = demo_scan("egr")
        scan["readings"]["HIDDEN_SECRET"] = {"value": 555, "unit": "oops", "status": "ok"}
        context = diagnostic_context(
            {"mode": "demo", "sensors": {"RPM": 790, "secret": "private"}, "units": {}},
            [], scan,
        )
        self.assertEqual(context["targeted_scan"]["profile"], "egr")
        self.assertNotIn("HIDDEN_SECRET", str(context))
        self.assertNotIn("private", str(context))
        self.assertIn("COMMANDED_EGR", context["targeted_scan"]["readings"])
        result = answer("Proveri EGR", context, "offline")
        self.assertIn("EGR", result)


if __name__ == "__main__":
    unittest.main()
