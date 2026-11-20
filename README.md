# AutoFX — Automotive Diagnostics Workstation

AutoFX je **Python desktop aplikacija za OBD-II dijagnostiku**, sa profesionalnim PySide6 interfejsom, grafikonima senzora, pregledom DTC grešaka, AI Mechanic asistentom, ciljanim dijagnostičkim profilima i servisnim demo režimom.

**Platforme:** Ubuntu/Linux i Windows 10/11. Aplikacija se trenutno pokreće iz izvornog koda; **Windows `.exe` instalater još nije objavljen**.

> **Važno:** Demo režim je simulator. Podrška za funkcije stvarnog vozila zavisi od ECU-a i ELM327 adaptera. Stvarne servisne operacije izvršavaj samo uz ovlašćenje vlasnika, sa vozilom bezbedno zaustavljenim. AI ne upravlja ECU-om.

## Funkcionalnosti

| Modul | Opis |
| --- | --- |
| Overview | RPM, brzina, temperatura rashladne tečnosti, opterećenje, gas i grafikon |
| Diagnostics | DTC lista, detalji izabrane greške, AI objašnjenje |
| Parameters | Pregled, validacija, potvrda i zapis **simuliranih** promena parametara |
| Sessions | Lokalne JSONL evidencije dijagnostike i servisnih operacija |
| AI Assistant | Lokalna pravila bez interneta ili opcioni OpenAI razgovor |
| Targeted Diagnostics | Generički profili Engine, EGR, DPF i SCR; nepodržani PID-ovi ostaju označeni |

## Preduslovi

- **Python 3.10+**, preporuka **Python 3.12** (64-bit), sa `venv` podrškom.
- **Git** (za kloniranje repozitorijuma).
- Internet pri prvoj instalaciji zavisnosti.
- ELM327 **Bluetooth Classic / SPP** adapter za testiranje na stvarnom vozilu. Demo režim ne zahteva adapter.
- OpenAI API ključ **samo** ako želiš cloud AI razgovor; nije potreban za lokalni/demo režim.

## 🐧 Instalacija — Ubuntu / Linux

Na Ubuntu 24.04 (ili sličnom Debian/Ubuntu sistemu) otvori Terminal.

**1. Instaliraj sistemske zavisnosti:**

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip libxcb-cursor0 bluez
```

**2. Preuzmi AutoFX:**

```bash
git clone https://github.com/tomkaboris/autofx.git
cd autofx
```

**3. Napravi i aktiviraj virtualno okruženje:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**4. Instaliraj pakete:**

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Ako želiš i OpenAI integraciju, umesto poslednje komande instaliraj `requirements-ai.txt` (ona uključuje i osnovne zavisnosti):

```bash
python -m pip install -r requirements-ai.txt
```

**5. Pokreni desktop aplikaciju:**

```bash
python run_desktop.py
```

**Preporuka:** Na Linuxu koristi **`run_desktop.py`**, a ne `desktop.py`. Launcher rešava poznati konflikt Qt/GTK okruženja kada se aplikacija pokreće iz VS Code instaliranog preko Snap-a.

Ako želiš direktni Wayland režim i znaš da Qt podržava tvoje okruženje:

```bash
AUTOFX_QT_PLATFORM=wayland python run_desktop.py
```

### Linux: ELM327 Bluetooth povezivanje

1. Upari ELM327 **Bluetooth Classic** adapter u sistemskim Bluetooth podešavanjima.
2. Potreban je serijski port (npr. `/dev/rfcomm0`), koji možda moraš ručno da mapiraš kroz BlueZ/RFCOMM. Primer (zameni MAC adresu svojom):

   ```bash
   sudo rfcomm bind 0 AA:BB:CC:DD:EE:FF
   ```

3. Proveri dostupne portove:

   ```bash
   python main.py --list-ports
   ```

4. U aplikaciji izaberi **ELM327 serial**, unesi `/dev/rfcomm0` i klikni **Connect**. Ako dobiješ `Permission denied`, proveri dozvole serijskog uređaja i pripadnost odgovarajućoj grupi (često `dialout`).

Bluetooth uparivanje samo po sebi ne potvrđuje da je ECU povezan. Kontakt treba da bude uključen za odgovarajuće dijagnostičke operacije; vozilo mora biti parkirano.

## 🪟 Instalacija — Windows 10/11

**1. Instaliraj:**

- **Python 3.12 (64-bit)** sa [python.org](https://www.python.org/downloads/windows/) — pri instalaciji uključi opciju **Add Python to PATH**, ako je ponuđena.
- **Git for Windows** sa [git-scm.com](https://git-scm.com/download/win).

**2. Otvori PowerShell i kloniraj projekat:**

```powershell
git clone https://github.com/tomkaboris/autofx.git
cd autofx
```

**3. Napravi virtualno okruženje:**

```powershell
py -3 -m venv .venv
```

**4. Instaliraj zavisnosti bez potrebe za aktivacijom okruženja:**

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Za OpenAI integraciju možeš koristiti `requirements-ai.txt` umesto `requirements.txt`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ai.txt
```

**5. Pokreni AutoFX:**

```powershell
.\.venv\Scripts\python.exe run_desktop.py
```

> Ovaj način radi i kada PowerShell zabranjuje izvršavanje `Activate.ps1` skripte — nije potrebno menjati `ExecutionPolicy`.

### Windows: ELM327 Bluetooth povezivanje

1. Uključi adapter u OBD-II port i upari ga u **Settings → Bluetooth & devices**.
2. U **Device Manager** ili Bluetooth COM port podešavanjima pronađi **outgoing Serial Port (COMx)**.
3. U AutoFX izaberi **ELM327 serial**, odaberi/upiši odgovarajući port (npr. `COM5`) i klikni **Connect**.

Ako port nije prikazan, proveri da adapter podržava **Bluetooth Classic SPP**. Neki BLE i Wi-Fi ELM327 adapteri zahtevaju drugačiji transport i nisu podržani ovom verzijom.

## 🧪 Prvo pokretanje — demo režim

1. Pokreni `run_desktop.py`.
2. Izaberi **Demo simulator** i klikni **Connect**.
3. U **Overview** proveri da se senzori i RPM grafikon osvežavaju.
4. U **Diagnostics** izaberi simuliranu grešku `P0300` za prikaz detalja.
5. U **AI Assistant** izaberi **Local analysis (offline)** i klikni **Analyze snapshot** (lokalna pravila, nije LLM).
6. U **Parameters** promeni simuliranu vrednost, klikni **Preview → Apply in simulator** i potvrdi. Stvarni ECU se ne menja.

Za demo proveru globalnog brisanja DTC podataka: **Diagnostics → Demo: simulate engine OFF**, sačekaj `RPM = 0`, pa koristi **Clear emissions DTCs (Mode 04)**, prihvati upozorenje i ukucaj `CLEAR ALL`. Operacija je **isključivo simulirana** u Demo režimu.

## 🤖 OpenAI AI Mechanic — opciono

`Local analysis (offline)` koristi jednostavna pravila i ne daje slobodan razgovor nalik LLM-u. Za razgovorni AI instaliraj `requirements-ai.txt`, obezbedi sopstveni **OpenAI API ključ** i pokreni AutoFX sa tom promenljivom okruženja.

**Linux:**

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
python run_desktop.py
```

**Windows PowerShell:**

```powershell
$env:OPENAI_API_KEY = "YOUR_API_KEY"
.\.venv\Scripts\python.exe run_desktop.py
```

U **AI Assistant** izaberi **OpenAI cloud (explicit opt-in)**. Cloud zahtev se šalje tek kada pritisneš **Ask AI** ili **Analyze snapshot**. Šalju se pitanje i ograničen trenutni dijagnostički snimak, ne ceo log. Ne stavljaj API ključ u kod, Git ili screenshotove. Korišćenje OpenAI API-ja plaća se posebno od ChatGPT pretplate. Model možeš promeniti promenljivom `AUTOFX_OPENAI_MODEL` ako je dostupan na tvom API nalogu.

## ✅ Testiranje

U aktivnom okruženju na Linuxu:

```bash
python -m unittest discover -s tests -v
```

Na Windowsu bez aktivacije:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

CLI simulator, ako ne želiš da pokrećeš GUI:

```bash
python main.py --demo --count 5
```

## 🔄 Ažuriranje instalacije

U postojećem direktorijumu projekta:

**Linux:**

```bash
git checkout main
git pull origin main
source .venv/bin/activate
python -m pip install -r requirements-ai.txt
python run_desktop.py
```

**Windows PowerShell:**

```powershell
git checkout main
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r requirements-ai.txt
.\.venv\Scripts\python.exe run_desktop.py
```

Ako ne koristiš OpenAI, zameni `requirements-ai.txt` sa `requirements.txt`. Ako imaš lokalne necommitovane izmene, sačuvaj ih pre `git pull`.

## Troubleshooting

| Simptom | Šta proveriti |
| --- | --- |
| Linux: `Settings schema ... xsettings ... antialiasing` | Pokreći `python run_desktop.py` (čisti VS Code Snap GTK/GIO okruženje). |
| Linux: `Could not load Qt platform plugin xcb` | Proveri `libxcb-cursor0`, XWayland i Qt instalaciju; ako je potrebno, probaj `AUTOFX_QT_PLATFORM=wayland`. |
| `ModuleNotFoundError` | Proveri da si u odgovarajućem virtualnom okruženju i ponovi `pip install -r requirements.txt`. |
| `Permission denied: /dev/rfcomm0` | Proveri dozvole uređaja i korisničku grupu; nemoj pokretati celu GUI aplikaciju kao root. |
| Windows: `COMx` nije prikazan | Proveri Bluetooth SPP uparivanje i outgoing COM port. |
| Uparen adapter, ali nema ECU podataka | Proveri kontakt, adapter, port i podršku vozila za standardne OBD-II PID-ove. |
| AI javlja da nema `OPENAI_API_KEY` | Postavi ključ u *istom* terminalu pre pokretanja aplikacije ili koristi offline režim. |

## Bezbednost i ograničenja

- Standardni ELM327 **nije univerzalni OEM programator**. Neki proizvođački PID-ovi i servisne adaptacije zahtevaju drugačiji interfejs i zvanične procedure.
- **Mode 04** nije brisanje pojedinačne greške: može obrisati sve podržane emisijske DTC podatke, uključujući freeze-frame, i resetovati readiness monitore. Trajni kodovi mogu ostati. Sačuvaj izveštaj **pre** brisanja.
- Prikaz **Parameters** menja samo simulator, ne stvarni ECU.
- AI ne izvršava ECU komande niti programiranje.
- DPF/SCR profili daju samo **generički kontekst**, ne garantuju očitavanje čađi, NOx ili doziranja AdBlue-a.
- Logovi u `logs/` mogu sadržati podatke o vozilu; ne objavljuj ih bez provere.
- Stvarna ECU kompatibilnost i Windows rad **nisu potpuno verifikovani** na svim vozilima i računarima.

## Dodatna dokumentacija

- [Desktop GUI](docs/DESKTOP.md)
- [AI Mechanic](docs/AI_MECHANIC.md)
- [Targeted diagnostics](docs/TARGETED_DIAGNOSTICS.md)
- [Service workspace](docs/SERVICE_WORKSPACE.md)
- [Parameter management](docs/PARAMETERS.md)

---

Razvoj: [tomkaboris/autofx](https://github.com/tomkaboris/autofx) · Podrazumevana grana: `main`
