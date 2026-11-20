# AutoFX Desktop — real-vehicle-only

Pokretanje posle instalacije:

```bash
python run_desktop.py
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe run_desktop.py
```

Desktop više nema simulator niti lažna očitavanja. Pokreće se bez adaptera, ali vrednosti se prikazuju isključivo nakon povezivanja stvarnog ELM327 serijskog adaptera i uspešne komunikacije sa ECU-om.

Izaberi serijski port (/dev/rfcomm0 ili COMx) i klikni **Connect**. Glavni ekran prikazuje podržane senzore. Nepodržani PID ostaje prazan.

Za Linux/Ubuntu je preporučen `run_desktop.py` zbog VS Code Snap/GTK konflikta.

Detaljne instalacione komande nalaze se u [README](../README.md).
