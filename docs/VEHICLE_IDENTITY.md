# AutoFX Vehicle & ECU identification

This module uses **real ELM327 + ECU responses only**. On connection, it checks advertised Mode 01 PID support and reads the following standard Mode 09 fields when available:

- VIN (validated as 17 characters; invalid responses are treated as unavailable)
- Calibration ID (CALID) and calibration verification number (CVN), if the ECU and python-OBD adapter support the queries
- Reported OBD protocol and serial port

**What this does not do:** guessing the make/model/year, discovering every module in the car, manufacturer-specific UDS routines, coding/adaptations, or sending write commands. Generic Mode 01 support does not imply OEM access.

## Running

```bash
git checkout main
git pull origin main
python -m unittest discover -s tests -v
python run_desktop.py
```

Connect a real Bluetooth Classic ELM327 serial port. Open the **Vehicle** page to inspect the identity and the advertised PID matrix. Missing responses are shown as **Unavailable**.

Mode 09 support depends heavily on the vehicle and python-OBD implementation. Some adapters expose no VIN/CALID/CVN despite functioning generic telemetry. This is not a reason to invent a vehicle identity.

## Privacy

The full VIN is considered sensitive vehicle data. The **Vehicle** page displays the VIN locally if the ECU returns a valid value. VIN is **not included in the default JSONL session or the AI Mechanic cloud context**. Existing telemetry and DTC logging is unchanged.

## Implementation notes

Identity queries run on the existing serial acquisition thread before normal polling; the GUI is not blocked by serial I/O. Nothing is queried or displayed until an actual vehicle connects. Values are reset on a new session and on disconnect.

## Known limitations

- No full multi-ECU discovery. python-OBD chiefly supports the engine/generic emissions interface.
- Mode 09 queries are best effort; some ECUs may reject them or respond with multiple messages the library cannot decode.
- Do not use this feature as proof of ECU firmware integrity or provenance.
