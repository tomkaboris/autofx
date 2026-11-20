"""Read-only OBD-II adapter and demo simulator."""
from __future__ import annotations
import random
from datetime import datetime, timezone
from typing import Any

SENSORS = ("RPM", "SPEED", "COOLANT_TEMP", "ENGINE_LOAD", "THROTTLE_POS")

def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

class DemoAdapter:
    def __init__(self) -> None:
        self.step = 0

    def connect(self) -> str:
        return "DEMO - simulated vehicle (not a real ECU)"

    def read(self) -> dict[str, Any]:
        self.step += 1
        return {
            "timestamp": timestamp(), "mode": "demo",
            "sensors": {
                "RPM": round(760 + random.uniform(-35, 35), 1),
                "SPEED": 0,
                "COOLANT_TEMP": 85 + random.randint(-2, 2),
                "ENGINE_LOAD": round(19 + random.uniform(-3, 3), 1),
                "THROTTLE_POS": round(12 + random.uniform(-1, 1), 1),
            },
            "units": {"RPM": "rpm", "SPEED": "km/h", "COOLANT_TEMP": "degC", "ENGINE_LOAD": "%", "THROTTLE_POS": "%"},
        }

    def dtcs(self) -> list[dict[str, str]]:
        return [{"code": "P0300", "description": "Simulated example code, not a diagnosis"}]

    def close(self) -> None:
        pass

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

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None
