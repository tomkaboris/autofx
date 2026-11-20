# AutoFX Desktop v0.2

Professional read-only automotive diagnostic UI built with PySide6.

## Quick start — Ubuntu 24.04

```bash
sudo apt update
sudo apt install python3-venv libxcb-cursor0
git clone https://github.com/tomkaboris/autofx.git
cd autofx
git checkout feat/professional-desktop-ui
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python desktop.py
```

Select **Demo simulator** and press **Connect**. The Overview displays simulated RPM, speed, coolant, load and throttle data with a live chart. Diagnostics displays a sample DTC (P0300) clearly marked as simulated. Disconnect to end the session; the JSONL log is in `logs/`.

## Windows 11 (PowerShell)

```powershell
git clone https://github.com/tomkaboris/autofx.git
cd autofx
git checkout feat/professional-desktop-ui
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python desktop.py
```

If PowerShell blocks activation, invoke `.venv\Scripts\python.exe` directly, e.g. `.venv\Scripts\python.exe desktop.py`.

## ELM327 Bluetooth Classic

1. Pair the adapter via the operating system Bluetooth settings, with ignition on and vehicle parked.
2. On Linux configure your paired device's RFCOMM serial mapping (commonly `/dev/rfcomm0`) and check permissions. On Windows find the adapter's outgoing Bluetooth Serial Port (COMx).
3. Select **ELM327 serial**, refresh the port list, pick or type the port, then **Connect**.
4. Wait for the connection status. Bluetooth pairing alone does not confirm ECU communication. Unsupported PIDs show “—”.

**Caution:** The application only performs standard OBD-II reads. It does not clear faults, operate actuators, reflash ECU firmware or disable emissions systems. Keep the laptop and adapter connected only when it is safe to do so; no interactive operation while driving.

## Current scope

- Overview dashboard with five sensor cards and RPM chart
- Diagnostics page showing stored DTCs
- Session recording to local JSONL
- Demo simulator, serial-port chooser, connect/disconnect
- AI Assistant placeholder (not yet integrated)

### Limitations

- UI and cross-platform compatibility must be verified on the target Ubuntu/Windows machines.
- Actual ECU compatibility depends on vehicle, ELM327 firmware and accessible PIDs.
- The first iteration supports one active session at a time.
- The UI opens sessions but does not yet replay/import past logs or provide interactive AI assistance.
