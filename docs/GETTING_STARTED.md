# AutoFX v0.1 — Linux and Windows

AutoFX is a **read-only** OBD-II CLI proof of concept. Use the adapter on a stationary vehicle with ignition on. Bluetooth pairing is not the same as an established ECU connection.

## Ubuntu/Linux

```bash
sudo apt install python3-venv bluez
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --demo --count 5
```

Pair the ELM327 Bluetooth Classic adapter through system Bluetooth settings. Establish an RFCOMM serial binding for the paired MAC address using your system's BlueZ configuration, then check its device path (commonly `/dev/rfcomm0`). Permissions or group membership may be required.

```bash
python main.py --list-ports
python main.py --port /dev/rfcomm0 --count 5
```

## Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py --demo --count 5
python main.py --list-ports
```

Pair the Bluetooth adapter in Windows Settings and locate its **outgoing serial COM port** in Device Manager/Bluetooth COM Ports.

```powershell
python main.py --port COM5 --count 5
```

Use `--baudrate 38400` only if the adapter needs it. Real adapters and ECUs may not support every PID. Session files are written to `logs/` as JSONL and should be treated as sensitive diagnostic data.

## Scope

No fault clearing, unrestricted CAN/UDS commands, ECU flashes, actuator control, or disabling of vehicle emissions systems. Planned: PySide6 desktop UI and permissioned AI analysis of logged data.
