# Targeted read-only diagnostics (AutoFX v0.4)

## Quick start

```bash
git fetch origin
git checkout feat/targeted-obd-diagnostics
python -m pip install -r requirements-ai.txt
python -m unittest discover -s tests -v
python run_desktop.py
```

**Demo test:** Connect -> AI Assistant -> choose profile -> **Read selected PIDs**. The result table reports values, units and statuses. Ask a question: AutoFX suggests the corresponding profile in the selector but **does not run it automatically**. Click **Read selected PIDs** to perform the scan, and **Analyze snapshot** to pass the latest scan to the offline rules or explicitly selected cloud model.

**Real ELM327 test:** Pair your Bluetooth Classic device; select ELM327 serial and the paired port (Linux RFCOMM or Windows COM port). With the vehicle parked and ignition enabled, connect and read a profile. Adapter access is serialized through the acquisition thread—there are no simultaneous serial requests from the AI thread.

## Included profiles

| Profile | Standard Mode 01 data | Limitations |
|---|---|---|
| Engine/Intake | RPM, speed, coolant, MAF, manifold pressure, air temp, load, fuel pressure, atmospheric pressure | Vehicle may not expose every PID |
| EGR/Air flow | Commanded EGR, EGR error, MAF, manifold pressure, RPM, load | Does not activate the valve or prove a fault |
| DPF/Exhaust | Catalyst temperature, RPM, load, coolant, speed, fuel rate | **Not** DPF differential pressure, soot level or regeneration status |
| SCR/AdBlue | Generic thermal, RPM/load and fuel rate context | **Not** urea injection/pressure or NOx readings |

All commands are built-in python-OBD standard read-only PIDs, invoked only when supported. No custom CAN, UDS writes, forced regeneration, resets, firmware modification or EGR/DPF/SCR deactivation.

## AI behavior

- The local classifier suggests which profile might be relevant to the question, without running it.
- The operator explicitly triggers a targeted read.
- The AI receives only allowlisted profile fields, five basic values, and DTCs.
- Unsupported PID responses remain marked unsupported; they are never guessed.
- Cloud requests remain opt-in and use current limited data only.
- Values are contextual hints, not independently verified mechanical diagnoses.

## Tests

```bash
python -m unittest discover -s tests -v
```

GUI startup and a real ELM327 connection require validation on your Ubuntu/Windows systems.
