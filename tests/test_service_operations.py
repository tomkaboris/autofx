"""Policy and simulator regression tests for supervised DTC clearing."""
import unittest
from datetime import datetime, timedelta, timezone

from obd_ai.adapter import DemoAdapter
from obd_ai.service_operations import (
    CONFIRMATION_TEXT, OperationDenied, validate_clear_request
)


def sample(rpm=0, speed=0, age_seconds=0):
    when = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    return {"mode": "demo", "timestamp": when.isoformat(),
            "sensors": {"RPM": rpm, "SPEED": speed}}


class ServiceOperationTests(unittest.TestCase):
    def test_requires_explicit_confirmation(self):
        with self.assertRaises(OperationDenied):
            validate_clear_request(mode="demo", sample=sample(),
                                   confirmed=False, text=CONFIRMATION_TEXT)
        with self.assertRaises(OperationDenied):
            validate_clear_request(mode="demo", sample=sample(),
                                   confirmed=True, text="yes")

    def test_requires_fresh_engine_off_and_stationary(self):
        for reading in (sample(rpm=780), sample(speed=2), sample(rpm=None),
                        sample(speed=None), sample(age_seconds=30)):
            with self.subTest(reading=reading), self.assertRaises(OperationDenied):
                validate_clear_request(mode="demo", sample=reading,
                                       confirmed=True, text=CONFIRMATION_TEXT)

    def test_cannot_authorize_with_mismatched_source(self):
        with self.assertRaises(OperationDenied):
            validate_clear_request(mode="vehicle", sample=sample(),
                                   confirmed=True, text=CONFIRMATION_TEXT)

    def test_only_exact_phrase_works(self):
        validate_clear_request(mode="demo", sample=sample(), confirmed=True,
                               text=CONFIRMATION_TEXT)

    def test_demo_clear_changes_only_simulator_codes(self):
        adapter = DemoAdapter()
        adapter.connect()
        before = adapter.dtcs()
        self.assertTrue(before)
        adapter.engine_running = False
        reading = adapter.read()
        validate_clear_request(mode="demo", sample=reading,
                               confirmed=True, text=CONFIRMATION_TEXT)
        result = adapter.clear_emissions_dtcs()
        self.assertEqual(result["mode"], "demo")
        self.assertEqual(result["result"], "simulated")
        self.assertEqual(adapter.dtcs(), [])
        adapter.close()


if __name__ == "__main__":
    unittest.main()
