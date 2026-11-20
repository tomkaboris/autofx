# AutoFX — Automotive Diagnostics Workstation

AutoFX je Python desktop dijagnostički alat za **stvarna vozila** i **ELM327 Bluetooth Classic** OBD-II adaptere. Profesionalni interfejs koristi PySide6 i PyQtGraph; svi parametri i DTC kodovi dolaze iz stvarne ECU komunikacije.

> **Nema simulacije:** aplikacija nema demo adapter, izmišljena očitavanja, simulirane DTC kodove ni simulirane promene parametara. Bez podržanog ELM327 porta nema podataka o vozilu.

## Trenutne mogućnosti

- **Overview:** RPM, brzina, temperatura rashladne tečnosti, opterećenje i gas; real-time grafikon.
- **Diagnostics:** očitani DTC kodovi i detalji; razgovor sa AI o izabranoj grešci.
- **Targeted diagnostics:** Engine, EGR, DPF/SCR profili sa generičkim, *stvarno dostupnim* OBD-II PID-ovima. Nepodržani PID prikazuje se kao nedostupan.
- **Service 04:** globalno brisanje podržanih emisijski povezanih DTC podataka, sa dvostrukom potvrdom, proverom stanja vozila i ponovnim očitavanjem. Ne briše proizvoljno izabranu grešku.
- **AI Assistant:** lokalni dijagnostički sažetak zasnovan na pravilima ili opciona OpenAI analiza.
- **Sessions:** JSONL zapisi očitavanja i servisnih operacija u direktorijumu `logs/`.

**Ne postoji univerzalni ECU editor.** Promene konfiguracionih parametara, kodiranje i proizvođačke adaptacije nisu omogućene dok se ne implementiraju i ne verifikuju za tačan ECU i odgovarajući adapter.

## Linux / Ubuntu instalacija

Preduslovi: Ubuntu 24.04 ili sličan, Python 3.10+, Git, Python venv, grafičko okruženje.

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip libxcb-cursor0 bluez

git clone https://github.com/tomkaboris/autofx.git
cd autofx

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_desktop.py
```

Na Linuxu koristi **`run_desktop.py`**, jer uklanja problematično GTK/GSettings okruženje nasleđeno iz VS Code Snap-a.

### Linux: Bluetooth Classic serijski port

Upari uređaj kroz Bluetooth podešavanja. Po potrebi mapiraj RFCOMM, zamenjujući adresu stvarnog adaptera:

```bash
sudo rfcomm bind 0 AA:BB:CC:DD:EE:FF
python main.py --list-ports
```

U GUI-ju unesi `/dev/rfcomm0` ili drugi stvarni port. Proveri dozvole za serijski uređaj (često grupa `dialout`). Ne pokreći GUI kao root.

CLI očitavanje na konkretnom portu:

```bash
python main.py --port /dev/rfcomm0 --count 5
```

## Windows 10/11 instalacija

Instaliraj Python 3.12 (64-bit) sa [python.org](https://www.python.org/downloads/windows/) i Git sa [git-scm.com](https://git-scm.com/download/win). Zatim u PowerShell-u:

```powershell
git clone https://github.com/tomkaboris/autofx.git
cd autofx

py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_desktop.py
```

Ne moraš da aktiviraš venv niti da menjaš PowerShell execution policy.

Upari ELM327 uređaj u **Settings → Bluetooth & devices**, pronađi njegov izlazni **Bluetooth Serial Port (COMx)** kroz Windows podešavanja ili Device Manager i u AutoFX izaberi npr. `COM5`.

Bluetooth Low Energy (BLE) ili Wi-Fi adapter možda ne radi sa postojećim serijskim ELM327 drajverom; ovaj projekat trenutno očekuje **Bluetooth Classic SPP**.

## Povezivanje sa stvarnim vozilom

1. Parkiraj vozilo i priključi kompatibilan ELM327 adapter u OBD-II konektor.
2. Upari uređaj sa računarom i proveri odgovarajući serijski port.
3. Uključi kontakt prema potrebama izabrane OBD procedure.
4. Pokreni aplikaciju i klikni **Connect**.
5. Podaci se pojavljuju samo ako ECU uspešno odgovara. Ako ne podržava PID, nema izmišljene zamenske vrednosti.

Stvarno brisanje DTC podataka može resetovati readiness monitore i ukloniti freeze-frame. Pre intervencije sačuvaj očitavanja. Za Service 04 motor mora biti ugašen, vozilo zaustavljeno, a RPM i SPEED moraju biti raspoloživi i 0 prema svežem ECU očitavanju. Neki ECU-ovi ne ispunjavaju ove uslove i tada aplikacija blokira operaciju.

## Opcioni OpenAI AI Mechanic

Lokalna analiza radi bez mreže, ali nije razgovorni jezički model. Za OpenAI cloud integraciju:

```bash
python -m pip install -r requirements-ai.txt
export OPENAI_API_KEY="YOUR_API_KEY"
python run_desktop.py
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ai.txt
$env:OPENAI_API_KEY = "YOUR_API_KEY"
.\.venv\Scripts\python.exe run_desktop.py
```

U AI Assistant ekranu izaberi **OpenAI cloud (explicit opt-in)**. U cloud se šalje samo ograničen aktuelni dijagnostički snimak i pitanje, tek nakon tvog klika. API se naplaćuje odvojeno od ChatGPT pretplate; ključ ne čuvaj u Git repozitorijumu.

## Testovi

Linux:

```bash
python -m unittest discover -s tests -v
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Testovi proveravaju validaciju i ponašanje programskih komponenti bez priključenog vozila. **Test fixture nije demo režim** i testovi ne tvrde da stvarni ECU podržava određenu funkciju.

## Ažuriranje

```bash
git checkout main
git pull origin main
python -m pip install -r requirements.txt
python run_desktop.py
```

Na Windowsu koristi `.venv\Scripts\python.exe` umesto `python`.

## Ograničenja i napomene

- Potrebna je stvarna komunikacija sa ECU-om; bez nje ne prikazujemo parametre.
- Nisu podržane proizvoljne ECU izmene, firmware pisanje ili proizvođačke adaptacije.
- Service 04 utiče na grupu emisijskih DTC podataka, ne nužno na sve proizvođačke ili trajne kodove.
- Generički ELM327 ne garantuje pristup čađi u DPF-u, NOx senzorima ili doziranju AdBlue-a.
- Napredne servisne intervencije obavljaj prema proizvođačkoj proceduri i uz saglasnost vlasnika.
- Nisu završena sveobuhvatna testiranja na različitim ECU-ovima i Windows konfiguracijama.

## Dokumentacija

- [Desktop](docs/DESKTOP.md)
- [AI Mechanic](docs/AI_MECHANIC.md)
- [Dijagnostički profili](docs/TARGETED_DIAGNOSTICS.md)
- [Service Workspace](docs/SERVICE_WORKSPACE.md)
