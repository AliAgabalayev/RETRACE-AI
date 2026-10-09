# Rule-Aware Visual Regression Prototype

A local tool that compares a **reference** game screenshot with a **candidate** screenshot under user-defined allow/deny rules and returns `PASS`, `FAIL` or `NEEDS_REVIEW`.

Flow: reference + candidate + rules -> alignment -> DINOv2 change proposals (plus a classical pixel-diff fallback) -> per-region VLM verdict on a BEFORE|AFTER crop -> whole-scene audit -> deterministic decision (`src/gameqa/decision.py`) -> bug report export (ZIP) or an explicit "approve as new reference".

Hypothesis under test, not assumed: DINOv2 patch-feature proposals help a VLM do rule-aware comparison. No accuracy target is claimed. Evaluation results (E2/E4) are in `docs/EXPERIMENTS.md`; at the time of writing they were still running.

**Status: working prototype, honest limits.** `VERIFIED` below means a status file, `docs/QA_REPORT.md`, senior-pm, or my own run in this session recorded the actual run. Everything else is `UNVERIFIED`.

## Stack and models

Python 3.13, Streamlit, PyTorch, OpenCV, Pillow, NumPy, Pydantic, pytest.

| Part | What actually runs | Notes |
| --- | --- | --- |
| Features | frozen DINOv2 ViT-S/14 `dinov2_vits14` via `torch.hub`, CUDA, fp32 | inference only |
| VLM | local Ollama `qwen2.5vl:3b`, prompt `v9` | runs on **CPU** (graph does not fit the 6 GB GPU); ~9.3 GiB free RAM needed at load; ~85 s median per uncached pair (docs/DECISIONS.md D10) |
| Mock judge | `--mock <behaviour>` / UI "MOCK" | fault injection only, always labelled, never FAIL/PASS |

No credentials are needed for the local setup (the cloud keys probed were expired, D2). No secrets live in the repo; if a cloud VLM is added later, keep its key in an environment variable and never in code or reports.

## Setup

| Step | Command | Status |
| --- | --- | --- |
| venv reusing system torch | `python3 -m venv --system-site-packages .venv` | VERIFIED (D1) |
| Streamlit | `.venv/bin/pip install streamlit` | VERIFIED (streamlit 1.65, senior-pm) |
| Editable install | `.venv/bin/pip install -e . --no-deps` | VERIFIED (senior-pm); the plain form without `--no-deps` is UNVERIFIED |
| VLM model | `ollama pull qwen2.5vl:3b` | VERIFIED (pulled and used, dl-engineer) |
| DINOv2 weights | fetched by `torch.hub` on first use | VERIFIED (loaded on Python 3.13 / torch 2.12, MODEL_NOTES section 1) |

If the VLM fails to load with "model requires more system memory": close heavy apps (browser) and run `ollama stop qwen2.5vl:3b`, then retry (QA-D6, D9).

## Run

| Purpose | Command | Status |
| --- | --- | --- |
| Tests | `.venv/bin/python -m pytest -q` | VERIFIED: 163 passed, 6 skipped (senior-pm; I re-ran it, 5.5 s). The 6 skipped are `real_model` tests gated by `GAMEQA_REAL=1` |
| Web app | `.venv/bin/streamlit run app.py` | VERIFIED to start (python-developer-app status: `/_stcore/health` returned ok). UI Analyze with the real VLM: UNVERIFIED by me |
| CLI, real engines | see below | VERIFIED (senior-pm) |
| CLI, mock judge | see below | VERIFIED by me this session |
| Fixtures | `.venv/bin/python scripts/make_fixtures.py [--out OUT] [--seed SEED]` | VERIFIED (qa-engineer status); I only ran `--help` |
| Data preparation | `.venv/bin/python scripts/prepare_data.py [--limit N] [--revision SHA] [--max-gb G]` | VERIFIED (data-prep status: 250 pairs); I only ran `--help` |
| Evaluation | `.venv/bin/python scripts/evaluate.py {predict,tune-classical,score} ...` | E1 VERIFIED (qa-engineer status); E2/E4 were running when this was written |

### CLI

```
.venv/bin/python -m gameqa.cli analyze --reference R.png --candidate C.png --rules rules.yaml \
    [--sample-id ID] [--json] [--config EXTRA.yaml] [--mock {allowed,forbidden,uncertain,timeout,invalid_json,unknown_rule}]
.venv/bin/python -m gameqa.cli batch --split {dev,eval,demo} [--manifest M.json] [--ids-file IDS.json] [--limit N] [--out results.jsonl] [--config ...] [--mock ...]
.venv/bin/python -m gameqa.cli approve --reference-id ID --run-id RUN_ID [--config ...]
```

Flags above are copied from `--help` (run by me). Observed runs:

| Command | Observed | Source |
| --- | --- | --- |
| `analyze` on `data/fixtures/object_removed` (real engines) | `FAIL`, real / complete, R1 forbidden D1. That run used the VLM disk cache, 3-4 s. Uncached, a pair takes ~85 s median on CPU | senior-pm |
| `analyze` on `lighting_change` (real) | `NEEDS_REVIEW` (R1 uncertain), real / complete | senior-pm |
| `analyze` on `allowed_and_forbidden` (real) | `FAIL` (R1 D1), real / complete | senior-pm |
| `analyze ... --mock timeout` on `object_removed` | `NEEDS_REVIEW  [MOCK: not real inference]`, mode `mock / degraded`, real DINOv2 on CUDA | me, 2026-10-09 |
| `analyze ... --mock allowed` on `object_removed` | same `NEEDS_REVIEW [MOCK]`: a mock "allowed" can never PASS | me |
| `approve --reference-id demo_ref --run-id <mock run>` | wrote `versions/v1.png` (original reference) and `v2.png` plus `history.json` | me, in a scratch directory |

All fixtures are **synthetic**, hand-drawn images (`data/fixtures/<case>/expected.json` has `"synthetic": true`). They say nothing about benchmark performance.

## Layout

```
app.py                      Streamlit UI
configs/default.yaml        thresholds, caps, timeouts, model names (all tunables)
configs/rules_example.yaml  the brief's A1/A2/D1/D2 example rules
src/gameqa/contracts.py     frozen Pydantic data contracts
src/gameqa/decision.py      the ONLY PASS/FAIL/NEEDS_REVIEW policy
src/gameqa/pipeline.py      analyze(): orchestration + artifacts
src/gameqa/storage.py       run dirs, atomic writes, ZIP export, reference versions
src/gameqa/cli.py           analyze / batch / approve
src/gameqa/vision/          alignment, features (DINOv2), proposals, judge (VLM), prompts
src/gameqa/data/            dataset preparation + manifests
scripts/                    prepare_data.py, evaluate.py, make_fixtures.py
tests/                      policy, acceptance, vision, app, data
data/fixtures/              SYNTHETIC test pairs
data/manifests/             inference_manifest.json (no labels), eval_labels.json (evaluation only)
artifacts/<run_id>/         per-run outputs (git-ignored)
references/<id>/            approved reference versions + history.json (git-ignored)
```

## Docs

- `docs/PROJECT_BRIEF.md` scope; `docs/DECISIONS.md` D1-D10 (policy changes: read D6, D9, D10)
- `docs/CODE_WALKTHROUGH.md` one real run traced through the functions
- `docs/DEMO_RUNBOOK.md` three demo cases + 5 benchmark pairs
- `docs/HANDOFF_DRAFT.md` Azerbaijani handoff draft (final `HANDOFF.md` is owned by senior-pm)
- `docs/MODEL_NOTES.md`, `docs/QA_REPORT.md`, `docs/EXPERIMENTS.md`, `docs/DATA_CARD.md`, `docs/READABILITY_FEEDBACK.md`, `docs/status/*.md`

## How results are labelled

Real benchmark data (VideoGameQA-Bench, CC BY 4.0), synthetic fixtures, real models (DINOv2, Ollama VLM), the classical fallback (pixel diff) and mocks (`is_mock=True`, model id `mock:*`) are always named separately. A mock result is never real inference. A run is `engine_mode: real | degraded | mock`; only component failures (provider error, timeout, exception) make a run `degraded`.

## Known limits (short)

Small-object misses at 14 px patch scale (the classical fallback catches some), alignment sensitivity (unreliable alignment blocks region-level FAIL), an uncalibrated 3B VLM (weak rule mapping, weak scene audit), CPU-only VLM latency, and a benchmark with only two distinct rule texts. Details: `docs/CODE_WALKTHROUGH.md` section 9.
