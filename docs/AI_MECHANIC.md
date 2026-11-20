# AutoFX AI Mechanic v0.3

AI Mechanic is a **read-only diagnostic assistant**. It receives only the latest standard OBD-II telemetry snapshot (five allowlisted PIDs) and up to 30 DTC entries. It has no access to serial ports, ECU command execution, firmware, or modifications. It does not perform repairs or remotely operate your car.

## Run on Ubuntu or Windows

From `feat/ai-mechanic-readonly`:

```bash
python -m pip install -r requirements.txt
python run_desktop.py
```

Select **Demo simulator**, click **Connect**, then visit **AI Assistant** and click **Analyze snapshot**. This works without a network connection or API key. It is a deterministic rule-based summary, **not** an LLM response.

### OpenAI cloud analysis (optional)

Install optional SDK:

```bash
python -m pip install -r requirements-ai.txt
```

Configure a secret in the shell (do **not** commit secrets to Git):

Linux:

```bash
export OPENAI_API_KEY='your-key-here'
export AUTOFX_OPENAI_MODEL='gpt-5.4-mini'
python run_desktop.py
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your-key-here"
$env:AUTOFX_OPENAI_MODEL="gpt-5.4-mini"
python run_desktop.py
```

In AI Assistant select **OpenAI cloud (explicit opt-in)**. A network request is made only when you click **Ask AI** or **Analyze snapshot** while that mode is selected. The app sends the question and the **current limited snapshot** (mode, timestamp, supported PIDs, units, DTC codes/descriptions), not the whole recording or serial port details. The request uses the Responses API with `store=False`. Provider-side handling is governed by its service settings and privacy terms; `store=False` is not a blanket guarantee of zero retention.

The model name can be changed via `AUTOFX_OPENAI_MODEL`; use one supported by your API account. Your ChatGPT subscription does **not** automatically include API credits.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Safety and limitations

- No executable AI tool calls, ECU writes, firmware changes, actuator operations, fault clearing or emissions-control disabling.
- The offline rules cover only a few generic signals; readings may use ECU-reported units. Do not rely on the application alone for repair decisions.
- Internet/cloud analysis may expose diagnostic information; explicitly select it only with proper customer authorization.
- Do not inspect or operate the app while driving.
- Cloud requests run in a background Qt thread. Close the app after the request ends.
