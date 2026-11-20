"""Guardrails for manually authorized OBD-II Service 04.

The API is deliberately narrow: one global emissions-related DTC clearing
operation. No per-code deletion or arbitrary ECU writes are exposed.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

CONFIRMATION_TEXT = "CLEAR ALL"
ACTION_NAME = "clear_emissions_dtc_mode04"


class OperationDenied(RuntimeError):
    pass


def validate_clear_request(*, mode: str, sample: dict | None,
                           confirmed: bool, text: str,
                           now: datetime | None = None) -> None:
    """Validate manual authorization and parked, engine-off live readings.

    May not be called by the AI assistant; only from an explicit UI action.
    A missing or stale reading is denied rather than assumed safe.
    """
    if not confirmed or text.strip() != CONFIRMATION_TEXT:
        raise OperationDenied("Explicit confirmation CLEAR ALL is required.")
    if mode != "vehicle":
        raise OperationDenied("A real OBD vehicle connection is required.")
    if not isinstance(sample, dict) or sample.get("mode") != mode:
        raise OperationDenied("Fresh telemetry from the same connected source is required.")
    sensors = sample.get("sensors", {})
    rpm, speed = sensors.get("RPM"), sensors.get("SPEED")
    if any(not isinstance(x, (int, float)) or isinstance(x, bool) or
           not math.isfinite(x) for x in (rpm, speed)):
        raise OperationDenied("Cannot confirm engine-off and stationary status: RPM/SPEED unavailable.")
    if rpm != 0 or speed != 0:
        raise OperationDenied("Engine must be stopped and vehicle stationary (RPM=0, SPEED=0).")
    try:
        observed = datetime.fromisoformat(str(sample["timestamp"]).replace("Z", "+00:00"))
        if observed.tzinfo is None:
            raise ValueError("Naive timestamp")
        age = ((now or datetime.now(timezone.utc)) - observed).total_seconds()
        if age < -2 or age > 10:
            raise OperationDenied("Telemetry is stale. Refresh readings and try again.")
    except (KeyError, TypeError, ValueError) as exc:
        raise OperationDenied("Cannot verify telemetry timestamp.") from exc


def operation_description() -> str:
    return (
        "OBD-II Service 04 clears ALL supported emissions-related stored DTCs, "
        "may erase freeze-frame information and resets readiness monitors. "
        "It is NOT a per-code delete. Permanent DTCs may remain until ECU "
        "monitor conditions are satisfied. Always document faults first."
    )
