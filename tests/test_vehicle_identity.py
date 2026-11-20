"""Real-vehicle identity normalization and read-only adapter tests.

Mocks are isolated test fixtures, never exposed as a runtime demo mode.
"""
import unittest
from unittest.mock import MagicMock

from obd_ai.adapter import Elm327Adapter
from obd_ai.vehicle_identity import build_identity, normalized_vin, SUPPORTED_PROFILE_COMMANDS


class VehicleIdentityTests(unittest.TestCase):
    def test_vin_must_be_real_obd_format(self):
        self.assertEqual(normalized_vin("WVWZZZ1JZXW000001"), "WVWZZZ1JZXW000001")
        for value in (None, "", "ABC", "INVALID VIN 123456", "I" * 17,
                      "O" * 17, "Q" * 17, 1234):
            with self.subTest(value=value):
                self.assertIsNone(normalized_vin(value))

    def test_unsupported_values_not_inferred(self):
        profile = build_identity(
            protocol="ISO 15765-4 CAN", port="/dev/rfcomm0",
            values={"VIN": None, "CALIBRATION_ID": None, "CVN": None},
            supported={"VIN": False, "RPM": True},
        )
        self.assertIsNone(profile["vin"])
        self.assertEqual(profile["vin_status"], "unsupported")
        self.assertIsNone(profile["calibration_id"])
        self.assertTrue(profile["supported_pids"]["RPM"])
        self.assertEqual(profile["supported_count"], 1)
        self.assertEqual(profile["total_checked"], len(SUPPORTED_PROFILE_COMMANDS))
        self.assertNotIn("make", profile)
        self.assertNotIn("model", profile)

    def test_invalid_vin_not_presented_as_valid(self):
        profile = build_identity(protocol=None, port=None,
                                 values={"VIN": "not-a-real-vin"},
                                 supported={"VIN": True})
        self.assertEqual(profile["vin_status"], "unavailable")
        self.assertIsNone(profile["vin"])

    def test_adapter_checks_support_before_reading_mode09(self):
        adapter = Elm327Adapter("/dev/null")
        command_objects = {name: object() for name in ("VIN", "CALIBRATION_ID", "CVN")}
        for name in SUPPORTED_PROFILE_COMMANDS:
            command_objects[name] = object()
        commands = MagicMock()
        for name, command in command_objects.items():
            setattr(commands, name, command)
        adapter.obd = MagicMock(commands=commands)
        adapter.connection = MagicMock()
        adapter.connection.is_connected.return_value = True
        adapter.connection.supports.side_effect = lambda c: c is command_objects["VIN"]
        adapter.connection.protocol_name.return_value = "CAN"
        adapter.connection.port_name.return_value = "/dev/ttyUSB0"
        adapter.connection.query.return_value = MagicMock(value="WVWZZZ1JZXW000001")
        adapter.connection.query.return_value.is_null.return_value = False
        result = adapter.identify_vehicle()
        self.assertEqual(result["vin"], "WVWZZZ1JZXW000001")
        self.assertEqual(adapter.connection.query.call_count, 1)
        adapter.connection.query.assert_called_once_with(command_objects["VIN"])
        self.assertEqual(result["supported_count"], 0)


if __name__ == "__main__":
    unittest.main()
