# Rule-Aware Game QA

Compare approved game screenshots with a new build under explicit rules, inspect changed regions, and export evidence-backed PASS / FAIL / NEEDS_REVIEW reports.

The final demo runtime is **OpenRouter / `google/gemini-3.5-flash` / reasoning low / prompt v9**, with frozen DINOv2 feature extraction and deterministic decision policy. Canonical configuration: `configs/openrouter_gemini_pilot.yaml`, merged config hash **eaa371255716**. Qwen is the historical comparison baseline, not the deployed runtime.

## Start

Use Python 3.12. Linux CPU setup:

```sh
python -m venv .venv
. .venv/bin/activate
pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
pip install --no-deps -e .
python scripts/start_deployment.py
```

The entrypoint selects the frozen configuration and seeds a checksum-verified historical barrel **FAIL** replay. Replay works without an API key and performs no new inference. Set **OPENROUTER_API_KEY** through host secrets for live analysis. Never commit a key. DINO downloads on first live analysis unless pre-cached; Docker pre-caches its exact source and weight identity.

Primary deployment: **Render Docker web service, at least 4 GB RAM / 2 CPU**. This is a capacity recommendation, not a measured hosted performance guarantee. [Deployment and owner checklist](docs/DEPLOYMENT.md), [Windows/video runbook](docs/FINAL_DEMO_RUNBOOK.md).

## Evidence and limits

- Portable saved run **20261009T123704Z-8e4e19**: barrel removal, validated forbidden/D1 and final FAIL. Export contains evidence.json, analysis.json, Markdown, inputs and crops. It is labelled replay.
- C2 is a **12-pair development diagnostic**, not held-out accuracy. Hybrid C and full-frame B each produced 1 PASS /4 FAIL /7 REVIEW, 41.7% decision coverage. Hybrid missed one of five frozen-label bugs: missing pedestal. REVIEW is abstention.
- Historical C2: 80 fresh calls, no retries, provider-reported cost $0.2871945. No DINO accuracy improvement or production readiness is claimed.
- Live uploads go to OpenRouter. Owner access/budget controls are needed before broad paid public use. Ephemeral storage supports replay; persistent storage is needed for durable history.

[C2 raw diagnostic](docs/CELAL_C2_OPENROUTER_PILOT.md), [freeze](docs/FINAL_IMPLEMENTATION_FREEZE.md), [third-party notices](THIRD_PARTY_NOTICES.md), [GitHub state](docs/FINAL_GITHUB_STATE.md).

## Checks

```sh
pip install pytest==8.3.4
python -m pytest -m 'not real_model' -q -ra
git diff --check
```

Real-model tests are opt-in and excluded from offline CI. CI builds the container, checks keyless health/replay/export, and loads frozen DINO on CPU without a VLM call. Frozen model, prompts, rules, thresholds and policy require explicit unblock before tuning.
