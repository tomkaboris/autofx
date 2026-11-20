"""AutoFX read-only OBD diagnostics CLI."""
from __future__ import annotations
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from obd_ai.adapter import DemoAdapter, Elm327Adapter

def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only ELM327 diagnostic logger")
    parser.add_argument("--port", help="Paired Bluetooth serial port, e.g. COM5 or /dev/rfcomm0")
    parser.add_argument("--baudrate", type=int)
    parser.add_argument("--demo", action="store_true", help="Simulated vehicle")
    parser.add_argument("--list-ports", action="store_true", help="List serial ports")
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--count", type=int, default=0, help="0 = until Ctrl+C")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.list_ports:
        from serial.tools import list_ports
        for port in list_ports.comports():
            print(f"{port.device} | {port.description}")
        return
    if args.interval < 0.5 or args.count < 0:
        parser.error("--interval must be >= 0.5 and --count must be >= 0")
    adapter = DemoAdapter() if args.demo else Elm327Adapter(args.port, args.baudrate)
    output = args.output or Path("logs") / f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        print(adapter.connect())
        print(f"Logging to: {output}")
        with output.open("a", encoding="utf-8") as logfile:
            try:
                dtc_data = {"type": "dtcs", "codes": adapter.dtcs()}
            except Exception as exc:
                dtc_data = {"type": "dtcs", "error": str(exc)}
            logfile.write(json.dumps(dtc_data, ensure_ascii=False) + "\n")
            print(json.dumps(dtc_data, ensure_ascii=False))
            i = 0
            while args.count == 0 or i < args.count:
                started = time.monotonic()
                reading = adapter.read()
                reading["type"] = "telemetry"
                logfile.write(json.dumps(reading, ensure_ascii=False) + "\n")
                logfile.flush()
                print(json.dumps(reading, ensure_ascii=False))
                i += 1
                if args.count and i >= args.count:
                    break
                time.sleep(max(0, args.interval - (time.monotonic() - started)))
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except (ConnectionError, OSError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
    finally:
        adapter.close()

if __name__ == "__main__":
    main()
