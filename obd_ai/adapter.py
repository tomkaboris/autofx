"""ELM327 OBD-II adapter for actual vehicle diagnostics."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from obd_ai.profiles import get_profile
from obd_ai.service_operations import ACTION_NAME
from obd_ai.vehicle_identity import (IDENTITY_COMMANDS, SUPPORTED_PROFILE_COMMANDS,
                                     build_identity)

SENSORS = ("RPM", "SPEED", "COOLANT_TEMP", "ENGINE_LOAD", "THROTTLE_POS")

def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

class Elm327Adapter:
    def __init__(self, port: str | None = None, baudrate: int | None = None) -> None:
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.obd = None

    def connect(self) -> str:
        import obd
        self.obd = obd
        kwargs = {"portstr": self.port, "fast": False, "timeout": 5}
        if self.baudrate:
            kwargs["baudrate"] = self.baudrate
        self.connection = obd.OBD(**kwargs)
        if not self.connection.is_connected():
            status = str(self.connection.status())
            self.close()
            raise ConnectionError(f"ECU connection failed ({status}); check ignition, Bluetooth and port.")
        return f"Connected: {self.connection.port_name()} | {self.connection.protocol_name()}"

    def identify_vehicle(self) -> dict[str, Any]:
        """Read the connected ECU's generic identification and advertised PIDs.

        Called only on the acquisition thread to serialize all serial access.
        Mode 09 is best effort: some adapters or vehicles return no values.
        """
        if self.connection is None or self.obd is None or not self.connection.is_connected():
            raise ConnectionError("ECU is not connected")
        supported: dict[str, bool] = {}
        values: dict[str, str | None] = {}
        for name in (*IDENTITY_COMMANDS, *SUPPORTED_PROFILE_COMMANDS):
            command = getattr(self.obd.commands, name, None)
            try:
                supported[name] = bool(
                    command is not None and self.connection.supports(command)
                )
            except (ValueError, AttributeError, OSError):
                supported[name] = False
        for name in IDENTITY_COMMANDS:
            if not supported.get(name):
                values[name] = None
                continue
            try:
                response = self.connection.query(getattr(self.obd.commands, name))
                values[name] = None if response.is_null() else str(response.value)
            except (AttributeError, ValueError, TypeError, OSError):
                values[name] = None
        return build_identity(
            protocol=str(self.connection.protocol_name() or ""),
            port=str(self.connection.port_name() or ""),
            values=values, supported=supported,
        )

    def read(self) -> dict[str, Any]:
        assert self.connection is not None and self.obd is not None
        values: dict[str, float | None] = {}
        units: dict[str, str | None] = {}
        for name in SENSORS:
            cmd = getattr(self.obd.commands, name)
            if not self.connection.supports(cmd):
                values[name], units[name] = None, None
                continue
            try:
                response = self.connection.query(cmd)
                if response.is_null():
                    values[name], units[name] = None, None
                else:
                    values[name] = round(float(response.value.magnitude), 2)
                    units[name] = str(response.value.units)
            except (ValueError, TypeError, AttributeError, OSError) as exc:
                values[name], units[name] = None, None
                print(f"Warning: {name}: {exc}")
        return {"timestamp": timestamp(), "mode": "vehicle", "sensors": values, "units": units}

    def dtcs(self) -> list[dict[str, str]]:
        assert self.connection is not None and self.obd is not None
        response = self.connection.query(self.obd.commands.GET_DTC)
        if response.is_null():
            return []
        return [{"code": str(code), "description": str(description)} for code, description in response.value]

    def clear_emissions_dtcs(self) -> dict[str, Any]:
        """Explicit Mode 04 service operation; never called autonomously.

        The transport response alone does not prove all codes were erased.
        Return a post-command re-read for operator interpretation.
        """
        if self.connection is None or self.obd is None or not self.connection.is_connected():
            raise ConnectionError("ECU is not connected")
        command = self.obd.commands.CLEAR_DTC
        # python-OBD marks CLEAR_DTC as not discoverable via the PID mask.
        # This explicit path is available only through the guarded service UI.
        self.connection.query(command, force=True)
        try:
            after = self.dtcs()
        except Exception as exc:
            return {"operation": ACTION_NAME, "mode": "vehicle",
                    "result": "unverified", "after": None, "error": str(exc),
                    "response_confirmed": False}
        return {"operation": ACTION_NAME, "mode": "vehicle",
                "result": "rechecked", "after": after,
                "response_confirmed": False}

    def read_profile(self, key: str) -> dict[str, Any]:
        """Read strictly allowlisted standard Mode 01 commands."""
        profile = get_profile(key)
        if self.connection is None or self.obd is None:
            raise ConnectionError("OBD adapter is not connected")
        readings: dict[str, dict[str, Any]] = {}
        for name in profile.commands:
            cmd = getattr(self.obd.commands, name, None)
            if cmd is None or not self.connection.supports(cmd):
                readings[name] = {"value": None, "unit": None, "status": "unsupported"}
                continue
            try:
                response = self.connection.query(cmd)
                if response.is_null():
                    readings[name] = {"value": None, "unit": None, "status": "unavailable"}
                else:
                    readings[name] = {
                        "value": round(float(response.value.magnitude), 2),
                        "unit": str(response.value.units),
                        "status": "ok",
                    }
            except (ValueError, TypeError, AttributeError, OSError) as exc:
                readings[name] = {"value": None, "unit": None, "status": "error"}
                print(f"Profile PID {name}: {exc}")
        return {
            "profile": key, "mode": "vehicle",
            "description": profile.description,
            "readings": readings,
        }

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None
