"""Conservative vehicle identity and generic OBD capability reporting.

No model/year inference, fabricated values, raw CAN requests or ECU writes.
VIN is sensitive; identification is shown in memory only and not added to logs
or AI payloads by default.
"""
from __future__ import annotations

import re
from typing import Any

from obd_ai.profiles import PROFILES


IDENTITY_COMMANDS = ("VIN", "CALIBRATION_ID", "CVN")
SUPPORTED_PROFILE_COMMANDS = tuple(sorted({
    pid for profile in PROFILES.values() for pid in profile.commands
}))
VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


def normalized_vin(raw: Any) -> str | None:
    """Keep only genuine, structurally valid 17-character VIN responses."""
    if not isinstance(raw, str):
        return None
    vin = raw.strip().upper()
    return vin if VIN_PATTERN.fullmatch(vin) else None


def normalize_reading(raw: Any, *, limit: int = 128) -> str | None:
    if raw is None:
        return None
    result = str(raw).strip().replace("\x00", "")
    return result[:limit] if result else None


def build_identity(
    *, protocol: str | None, port: str | None,
    values: dict[str, str | None], supported: dict[str, bool],
) -> dict[str, Any]:
    """Normalize actual results; unsupported values remain None."""
    actual_vin = normalized_vin(values.get("VIN"))
    counts = {key: bool(supported.get(key, False)) for key in SUPPORTED_PROFILE_COMMANDS}
    return {
        "status": "connected",
        "vin": actual_vin,
        "vin_status": (
            "available" if actual_vin else
            "unsupported" if values.get("VIN") is None and not supported.get("VIN", False)
            else "unavailable"
        ),
        "protocol": normalize_reading(protocol, limit=96),
        "port": normalize_reading(port, limit=120),
        "calibration_id": normalize_reading(values.get("CALIBRATION_ID")),
        "calibration_verification": normalize_reading(values.get("CVN")),
        "supported_pids": counts,
        "supported_count": sum(counts.values()),
        "total_checked": len(counts),
        "note": (
            "Generic OBD-II reports selected Mode 01/09 data; it does not enumerate "
            "every vehicle ECU or prove that OEM coding/adaptations are available."
        ),
    }
