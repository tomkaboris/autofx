"""Safety policy tests for real vehicle Service 04 authorization."""
import unittest
from datetime import datetime, timedelta, timezone
from obd_ai.service_operations import (
    CONFIRMATION_TEXT, OperationDenied, validate_clear_request,
)


def telemetry(rpm=0, speed=0, seconds_old=0, mode="vehicle"):
    stamp = datetime.now(timezone.utc) - timedelta(seconds=seconds_old)
    return {"mode": mode, "timestamp": stamp.isoformat(),
            "sensors": {"RPM": rpm, "SPEED": speed}}


class ServicePolicyTests(unittest.TestCase):
    def test_confirmation_is_mandatory(self):
        for confirmed, text in ((False, CONFIRMATION_TEXT), (True, "yes")):
            with self.assertRaises(OperationDenied):
                validate_clear_request(mode="vehicle", sample=telemetry(),
                                       confirmed=confirmed, text=text)

    def test_engine_off_stationary_and_fresh(self):
        for reading in (telemetry(rpm=700), telemetry(speed=3), telemetry(rpm=None),
                        telemetry(speed=None), telemetry(seconds_old=30)):
            with self.subTest(reading=reading), self.assertRaises(OperationDenied):
                validate_clear_request(mode="vehicle", sample=reading,
                                       confirmed=True, text=CONFIRMATION_TEXT)

    def test_only_real_vehicle(self):
        with self.assertRaises(OperationDenied):
            validate_clear_request(mode="demo", sample=telemetry(mode="demo"),
                                   confirmed=True, text=CONFIRMATION_TEXT)

    def test_valid_manual_authorization(self):
        validate_clear_request(mode="vehicle", sample=telemetry(),
                               confirmed=True, text=CONFIRMATION_TEXT)


if __name__ == "__main__":
    unittest.main()
