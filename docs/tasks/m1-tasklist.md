# Milestone 1 task list (senior-pm, 2026-10-09)

Goal: runnable vertical slice — image pair + rules → proposals → crops → judgments → decision → report / reference approval — with REAL DINOv2 + REAL VLM (Ollama `qwen2.5vl:3b`), then evaluation and handoff.

Read first: `docs/PROJECT_BRIEF.md`, `docs/DECISIONS.md` (D1–D5 frozen interfaces), `AGENTS.md`.

## Shared rules (all agents)
- Python: always `.venv/bin/python` / `.venv/bin/pip`. Package is installed editable (`pip install -e .`); `import gameqa` works everywhere.
- `pyproject.toml` owner: python-developer (APP). Others request dependency changes via their status file; do not edit it.
- `src/gameqa/contracts.py` and `src/gameqa/decision.py` are FROZEN. Changes only via senior-pm (write the request + reason in your status file).
- Write only the files you own (table below). Each agent keeps `docs/status/<agent>.md` current (done / in progress / blockers / next), updated at least at every sub-milestone.
- Never `git commit` (senior-pm routes git through git-workflow-master). No remote operations.
- No background processes (`&`), no sleeps to wait. Long downloads are fine in the foreground.
- Mocks are labelled (`is_mock=True`, model id `mock:*`). Never present mock output as real inference.
- Held-out labels never reach inference inputs (only `data/manifests/eval_labels.json` holds them).
- GPU: RTX 3060 6 GB shared by DINOv2 (~100 MB) and Ollama qwen2.5vl:3b (~3–4 GB). Don't load other big models.

## Ownership
| Owner | Files |
| --- | --- |
| python-developer (DATA) | `src/gameqa/data/*.py`, `scripts/prepare_data.py`, `data/` contents (except fixtures), `docs/status/data-prep.md` |
| python-developer (APP) | `pyproject.toml`, `app.py`, `src/gameqa/{pipeline,storage,cli,config,rules,report,imageio}.py`, `configs/*.yaml`, `tests/app/`, `docs/status/python-developer-app.md` |
| dl-engineer | `src/gameqa/vision/*`, `tests/vision/`, `docs/MODEL_NOTES.md`, `artifacts/dl_smoke/`, `docs/status/dl-engineer.md` (config keys under `features/proposals/vlm/alignment`: send edits to APP owner, or edit only those sections) |
| qa-engineer | `tests/conftest.py`, `tests/policy/`, `tests/acceptance/`, `data/fixtures/`, `scripts/make_fixtures.py`, `scripts/evaluate.py`, `docs/QA_REPORT.md`, `docs/status/qa-engineer.md` |
| experiment-tracker-pm | `docs/EXPERIMENTS.md`, `docs/DATA_CARD.md`, `THIRD_PARTY_NOTICES.md`, `docs/status/experiment-tracker-pm.md`, `artifacts/eval/` summaries |
| documentation-engineer | `README.md`, `docs/CODE_WALKTHROUGH.md`, `docs/DEMO_RUNBOOK.md`, `docs/READABILITY_FEEDBACK.md`, `docs/HANDOFF_DRAFT.md`, `docs/status/documentation-engineer.md` |
| senior-pm | `docs/DECISIONS.md`, `docs/tasks/*`, `docs/status/senior-pm.md`, `HANDOFF.md`, integration fixes by agreement |

## Data contract (DATA → everyone)
- `data/manifests/inference_manifest.json`: list of `{sample_id, reference_path, candidate_path, rules:[{id,effect,description}], question, split, group_id|null, dataset_revision, sha256_reference, sha256_candidate, width/height per image, validation_status}`. NO labels. Paths relative to repo root.
- `data/manifests/eval_labels.json`: `{sample_id: {ground_truth_raw, label: "bug"|"no_bug"|null, split}}`.
- `gameqa.data.manifest.load_inference_manifest(path=None) -> list[dict]`, `load_eval_labels(path=None) -> dict`, `rules_from_question(question:str) -> list[Rule]`.
- Splits: `demo` (≤5), `dev` (~15%), `eval` (rest). Seeded, grouped by scene/source if known.

## Fixture contract (QA → everyone)
- `data/fixtures/<case>/{reference.png,candidate.png,rules.yaml,expected.json}`; `expected.json` = `{expected_decision: PASS|FAIL|NEEDS_REVIEW|any_not_PASS, changed_boxes:[[x1,y1,x2,y2],...], synthetic: true, notes}`. Synthetic, clearly labelled.
