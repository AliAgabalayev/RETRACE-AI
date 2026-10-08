# Rule-Aware Visual Regression Prototype

A local tool that compares a **reference** game screenshot with a **candidate** screenshot under user-defined allow/deny rules and returns `PASS`, `FAIL` or `NEEDS_REVIEW`.

Flow: reference + candidate + rules -> DINOv2 change proposals (plus classical pixel-diff fallback) -> per-region VLM verdict with before/after crops -> whole-scene audit -> deterministic decision (`src/gameqa/decision.py`) -> bug report export or explicit "approve as new reference".

Hypothesis under test (not assumed): DINOv2 patch-feature proposals help a VLM do rule-aware comparison. No accuracy target is claimed.

**Status: work in progress.** Nothing below is claimed to work unless marked VERIFIED, and VERIFIED means a file under `docs/status/` or an artifact records that it was actually run. Last checked: see `docs/status/documentation-engineer.md`.

## Stack

Python 3.13, Streamlit, PyTorch (frozen DINOv2 ViT-S/14 `dinov2_vits14`, inference only), OpenCV, Pillow, NumPy, Pydantic, pytest. VLM: local Ollama `qwen2.5vl:3b` (decision D2: cloud keys probed were expired/placeholder).

## Setup

| Step | Command | Status |
| --- | --- | --- |
| venv reusing system torch | `python3 -m venv --system-site-packages .venv` | VERIFIED (docs/DECISIONS.md D1, status/senior-pm.md) |
| Streamlit | `.venv/bin/pip install streamlit` | VERIFIED (streamlit 1.65 in .venv, status/senior-pm.md) |
| Editable install | `.venv/bin/pip install -e .` | VERIFIED as `pip install -e . --no-deps` (status/senior-pm.md); plain form UNVERIFIED |
| VLM model | `ollama pull qwen2.5vl:3b` | VERIFIED (pulled; not yet run on an image per status/senior-pm.md) |
| DINOv2 weights | fetched via `torch.hub` (`facebookresearch/dinov2`) on first use | UNVERIFIED (Python 3.13 compatibility untested) |

No credentials are required for the default local setup. If a cloud VLM is added later, put its key in an environment variable (name to be recorded in `configs/default.yaml`); never in code or reports.

## Run

| Purpose | Command | Status |
| --- | --- | --- |
| Web app | `.venv/bin/streamlit run app.py` | UNVERIFIED (app.py not present when last checked) |
| CLI analysis | `.venv/bin/python -m gameqa.cli ...` (exact flags pending) | UNVERIFIED |
| Tests | `.venv/bin/python -m pytest` | UNVERIFIED |
| Data preparation | `.venv/bin/python scripts/prepare_data.py` | UNVERIFIED |
| Evaluation | `.venv/bin/python scripts/evaluate.py` | UNVERIFIED |

## Layout

```
app.py                      Streamlit UI (APP owner)
configs/default.yaml        thresholds, caps, timeouts, model names
src/gameqa/contracts.py     frozen Pydantic data contracts
src/gameqa/decision.py      the only PASS/FAIL/NEEDS_REVIEW policy
src/gameqa/pipeline.py      orchestration: analyze()
src/gameqa/storage.py       run dirs, atomic writes, report export, reference history
src/gameqa/vision/          alignment, features (DINOv2), proposals, judge (VLM)
src/gameqa/data/            dataset preparation + manifests
scripts/                    prepare_data.py, evaluate.py, make_fixtures.py
tests/                      policy, acceptance, vision, app
data/fixtures/              SYNTHETIC test pairs (labelled synthetic)
artifacts/<run_id>/         per-run outputs (git-ignored)
references/<id>/            approved reference versions + history.json
```

## Docs

- `docs/PROJECT_BRIEF.md` scope, `docs/DECISIONS.md` decisions D1-D5
- `docs/CODE_WALKTHROUGH.md` image-to-verdict path
- `docs/DEMO_RUNBOOK.md` three demo cases
- `docs/HANDOFF_DRAFT.md` Azerbaijani handoff draft (final `HANDOFF.md` is owned by senior-pm)
- `docs/READABILITY_FEEDBACK.md`, `docs/status/*.md`

## Data labelling used in these docs

Real benchmark data (VideoGameQA-Bench, CC BY 4.0) vs synthetic fixtures (`data/fixtures/`) vs real models (DINOv2, Ollama VLM) vs classical fallback (pixel diff) vs mocks (`is_mock=True`, model id `mock:*`) are always named separately. A mock result is never real inference.
