# AutoFX DTC Service Workspace

A technician-operated diagnostic service layer. This milestone adds a detailed
DTC selection interface and **one narrow Mode 04 operation**; it is not a
universal ECU parameter editor.

## What is supported

- Select a stored DTC, inspect its description and discuss it with AI Mechanic.
- Save a local JSONL session containing original DTCs and the service audit result.
- Trigger a **global emissions-related DTC clear (OBD-II Mode 04)** only after
  two manual confirmations, with fresh, same-source RPM=0 and SPEED=0 readings.
- The worker checks the vehicle state AGAIN on its own acquisition thread
  immediately before sending the one allowed write command.
- DTC codes are read back afterwards. The application reports a recheck, **not**
  proof of a completed repair or full memory erase.

## Important limitations

Mode 04 does **not** delete only the selected fault: it affects all supported
emissions-related diagnostic information, can delete freeze frames and reset
readiness monitors. Permanent DTC codes and manufacturer-specific module faults
may remain. Clearing a code cannot repair the underlying cause.

The application blocks clearing when RPM/SPEED is missing or stale. Some vehicles
do not provide usable engine-off RPM via a low-cost ELM327, so Mode 04 will not
be available through this implementation for those vehicles.

A failure or uncertain adapter response must be investigated manually. Do not
repeatedly clear codes to conceal a recurring fault. Keep original records.

## Demo test, without a vehicle

```bash
git fetch origin
git checkout feat/service-dtc-workspace
python -m pip install -r requirements-ai.txt
python -m unittest discover -s tests -v
python run_desktop.py
```

Select **Demo simulator → Connect → Diagnostics**. Select P0300 for its detail.
Click **Demo: simulate engine OFF** and wait for RPM to show 0 on the Overview.
Then click **Clear emissions DTCs (Mode 04)**, review the warning, confirm and
type `CLEAR ALL`. The simulator clears its sample DTC, records the operation,
and the UI updates the table. **No real ECU command is sent in Demo mode.**

## Real vehicle

Use only on a parked vehicle, ignition ON, engine OFF. Save fault history first.
Require the owner's authorization for interventions. Confirm that a compatible
adapter, vehicle and OBD service allow the operation before trying it.
Real vehicle writes have **not yet been verified in this release**.

## Roadmap: controlled parameter changes

A universal arbitrary parameter editor is not possible with generic OBD-II.
An OEM-adapter-based module could expose approved, documented adaptations
through vehicle-specific service definitions:
`parameter ID → readable current value → allowed range → preconditions →
preview → technician confirmation → write → readback → audit/rollback strategy`.

AI can explain/recommend a proposed change but cannot execute it. Never add
unrestricted raw CAN/UDS writes to the AI context. Emission-system defeat
and safety-system bypass operations are outside the planned capabilities.
