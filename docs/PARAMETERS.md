# AutoFX Parameters (v0.6 prototype)

This screen demonstrates a proper ECU adaptation **workflow**, without using a real ECU.

## Use

```bash
git fetch origin
git checkout feat/parameter-management-demo
python -m unittest discover -s tests -v
python run_desktop.py
```

1. Select **Demo simulator** and **Connect**.
2. Open **Parameters** in the left navigation.
3. Select a simulated parameter, enter a value in the allowed range.
4. Click **Preview**, then **Apply in simulator** and confirm.
5. Check the current value and `logs/parameter-demo-audit.jsonl` for the result.

Demo values include simulated idle target, cooling fan temperature threshold and speed warning threshold. They are **illustrative laboratory fields**, not real ECU PID definitions, OEM-supported adaptations, or live values.

On a real ELM327 connection, these write controls are disabled. They never reach the serial adapter. There are no raw CAN/UDS commands or firmware writes.

## Future architecture for supported OEM adaptations

Each permitted service operation will need a vehicle/ECU-specific definition: exact ECU identity, readback command, OEM-supported write command, permissions, numeric range, units, prerequisites, safety policy, preview, technician approval, result verification and audit. Some ECUs require professional interfaces and factory authorizations. The AI assistant can explain the change but must not act as a direct write channel.

**OpenAI is not automatically enabled by this change.** To chat with an LLM, install optional `requirements-ai.txt`, provide `OPENAI_API_KEY` and choose **OpenAI cloud** in the AI screen. The default Local analysis is rule-based, not conversational AI.
