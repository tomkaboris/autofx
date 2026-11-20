"""Demo-only ECU parameter workflow.

This is a local simulator. It MUST NOT access serial ports or be used to
claim an adaptation was performed on a physical vehicle.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


class ParameterError(ValueError):
    pass


@dataclass(frozen=True)
class ParameterDefinition:
    key: str
    name: str
    unit: str
    minimum: int
    maximum: int
    default: int
    description: str


DEFINITIONS = {
    "idle_target": ParameterDefinition(
        "idle_target", "Idle target (simulation)", "rpm", 650, 1000, 750,
        "Simulated requested idle speed. No actual ECU adaptation."
    ),
    "fan_trigger": ParameterDefinition(
        "fan_trigger", "Cooling fan threshold (simulation)", "°C", 85, 105, 96,
        "Simulated temperature threshold; never commands a real fan."
    ),
    "speed_warning": ParameterDefinition(
        "speed_warning", "Speed warning threshold (simulation)", "km/h", 30, 130, 90,
        "Simulated instrument warning threshold; not vehicle coding."
    ),
}


class DemoParameterStore:
    def __init__(self):
        self._values = {key: item.default for key, item in DEFINITIONS.items()}

    def read(self, key: str) -> dict[str, Any]:
        definition = self._definition(key)
        return {
            "key": key, "name": definition.name,
            "value": self._values[key], "unit": definition.unit,
            "minimum": definition.minimum, "maximum": definition.maximum,
            "description": definition.description, "mode": "demo",
        }

    @staticmethod
    def _definition(key: str) -> ParameterDefinition:
        if key not in DEFINITIONS:
            raise ParameterError("Unknown demo parameter")
        return DEFINITIONS[key]

    def preview(self, key: str, proposed: int) -> dict[str, Any]:
        definition = self._definition(key)
        if isinstance(proposed, bool) or not isinstance(proposed, int):
            raise ParameterError("New value must be an integer")
        if not definition.minimum <= proposed <= definition.maximum:
            raise ParameterError(
                f"Value must be between {definition.minimum} and {definition.maximum} {definition.unit}"
            )
        return {
            "mode": "demo", "parameter": key,
            "previous": self._values[key], "proposed": proposed,
            "unit": definition.unit, "status": "preview_only",
        }

    def apply(self, key: str, proposed: int, *, confirmed: bool) -> dict[str, Any]:
        preview = self.preview(key, proposed)
        if confirmed is not True:
            raise ParameterError("Technician confirmation is required")
        self._values[key] = proposed
        return {
            **preview, "status": "simulated_applied",
            "verified": self.read(key)["value"] == proposed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def reset(self):
        self._values = {key: item.default for key, item in DEFINITIONS.items()}
