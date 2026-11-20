"""Read-only diagnostic scan profiles.

All profile command names are from the python-OBD standard Mode 01 table.
DPF and SCR profiles intentionally contain only generic *related* signals:
a generic ELM327 cannot promise filter delta pressure, soot load, urea or
NOx sensors without manufacturer-specific support.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class DiagnosticProfile:
    key: str
    title: str
    description: str
    commands: tuple[str, ...]


PROFILES = {
    "engine": DiagnosticProfile(
        "engine", "Engine / Intake",
        "Basic intake, thermal and fuel-system signals.",
        ("RPM", "SPEED", "COOLANT_TEMP", "ENGINE_LOAD", "THROTTLE_POS",
         "INTAKE_PRESSURE", "INTAKE_TEMP", "MAF", "FUEL_PRESSURE", "BAROMETRIC_PRESSURE"),
    ),
    "egr": DiagnosticProfile(
        "egr", "EGR / Air flow",
        "Commanded EGR and generic intake-air signals; not an actuator test.",
        ("RPM", "ENGINE_LOAD", "COOLANT_TEMP", "MAF", "INTAKE_PRESSURE",
         "COMMANDED_EGR", "EGR_ERROR"),
    ),
    "dpf": DiagnosticProfile(
        "dpf", "DPF / Exhaust (generic)",
        "Generic exhaust temperature and load proxies only. No soot/differential-pressure claim.",
        ("RPM", "ENGINE_LOAD", "SPEED", "COOLANT_TEMP",
         "CATALYST_TEMP_B1S1", "CATALYST_TEMP_B1S2", "FUEL_RATE"),
    ),
    "scr": DiagnosticProfile(
        "scr", "SCR / AdBlue (generic)",
        "Generic context only; urea dosage and NOx sensors need OEM support.",
        ("RPM", "ENGINE_LOAD", "COOLANT_TEMP",
         "CATALYST_TEMP_B1S1", "CATALYST_TEMP_B1S2", "FUEL_RATE"),
    ),
}


def profile_for_question(question: str) -> str:
    """Deterministic suggestion, does not run a scan."""
    q = question.casefold()
    if any(word in q for word in ("adblue", "ad blue", "scr", "urea", "noₓ", "nox")):
        return "scr"
    if any(word in q for word in ("dpf", "filter čestica", "filter cestica", "regeneracij", "soot")):
        return "dpf"
    if any(word in q for word in ("egr", "eger", "recirkulacij")):
        return "egr"
    return "engine"


def get_profile(key: str) -> DiagnosticProfile:
    if key not in PROFILES:
        raise ValueError("Unsupported read-only diagnostic profile")
    return PROFILES[key]


def demo_scan(key: str) -> dict:
    """Simulated profile scan with unsupported signals explicitly represented."""
    profile = get_profile(key)
    dummy = {
        "RPM": (780, "rpm"), "SPEED": (0, "km/h"),
        "COOLANT_TEMP": (87, "degree_Celsius"), "ENGINE_LOAD": (21, "percent"),
        "THROTTLE_POS": (12, "percent"), "INTAKE_PRESSURE": (37, "kilopascal"),
        "INTAKE_TEMP": (28, "degree_Celsius"), "MAF": (7.4, "gram / second"),
        "FUEL_PRESSURE": (320, "kilopascal"), "BAROMETRIC_PRESSURE": (100, "kilopascal"),
        "COMMANDED_EGR": (14, "percent"), "EGR_ERROR": (-2, "percent"),
        "CATALYST_TEMP_B1S1": (240, "degree_Celsius"),
        "CATALYST_TEMP_B1S2": (220, "degree_Celsius"),
        "FUEL_RATE": (0.8, "liter / hour"),
    }
    return {
        "profile": key, "mode": "demo", "description": profile.description,
        "readings": {
            name: {"value": dummy[name][0], "unit": dummy[name][1], "status": "simulated"}
            if name in dummy else {"value": None, "unit": None, "status": "unsupported"}
            for name in profile.commands
        },
    }
