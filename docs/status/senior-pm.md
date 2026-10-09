# senior-pm status — resume point

Last updated: 2026-10-09, session 2 start (~hour 0.7). Agents DISPATCHED (see below).

**New session: read this file, `docs/DECISIONS.md`, `docs/PROJECT_BRIEF.md`, `AGENTS.md`, then continue from "Next actions".**

## Why the previous session stopped
The project agents in `.claude/agents/` were created mid-session, so the Agent tool could not find them by name (`python-developer`, `dl-engineer`, `qa-engineer`, `experiment-tracker-pm`, `documentation-engineer`, `senior-pm` → "Agent type not found"). The owner rejected the `general-purpose` stand-in. A fresh session loads them by name — use the real agent types.

## Done (verified)
- **Environment** (DECISIONS D1): `.venv` = Python 3.13 with `--system-site-packages` (reuses `torch 2.12.0+cu130`, torchvision 0.27, cv2 4.13, pydantic 2.12, numpy 2.3, pandas, pyarrow 24, huggingface_hub 1.8, httpx, pytest 9). `streamlit 1.65` installed into `.venv`. `torch.cuda.is_available()` = True. Not installed: scikit-image. Always run `.venv/bin/python`.
- **Hardware**: RTX 3060 Laptop 6 GB VRAM, 16 cores, 14 GB RAM (~6 GB free), disk ~40 GB free (92% used) → never download the full 33.4 GB dataset.
- **VLM probe** (DECISIONS D2): `OPENROUTER_API_KEY` → 401 "API key expired". `NVIDIA_NIM_API_KEY`, `KIMI_API_KEY` → 401; values look like placeholders. Decision: local Ollama (v0.21, http://localhost:11434). `qwen2.5vl:3b` **pulled successfully** (not yet tested on an image). Also installed: `moondream:latest`, `gemma2:9b` (text-only), `qwen2.5:0.5b` (text-only).
- **Frozen contracts** (DECISIONS D3/D4):
  - `src/gameqa/contracts.py` — Rule, PairInput, AlignmentResult, RegionProposal, RegionJudgment, SceneAudit, Coverage, Versions, AnalysisResult, enums. Not yet imported/tested.
  - `src/gameqa/decision.py` — single PASS/FAIL/NEEDS_REVIEW policy. Not yet tested.
  - `configs/default.yaml` — thresholds, caps (8 regions), timeouts (30 s, 2 attempts), deadline 300 s, vlm provider ollama/qwen2.5vl:3b.
  - `docs/DECISIONS.md` D4 — exact function signatures for alignment / features / proposals / judge / pipeline / storage.
- **Skeleton**: `src/gameqa/{__init__,vision/__init__,data/__init__}.py`, `tests/__init__.py`, dirs `scripts/ configs/ docs/status/ docs/tasks/ data/ artifacts/ references/`, `.gitignore` (data/raw, data/work, data/cache, artifacts/*, references/*, .venv, models/).
- **Git**: `git init` done, branch `master`, **no commits yet** (worktrees need a first commit).

## Not started
Data download, vision modules, pipeline/app, tests/fixtures, evaluation, docs (README, walkthrough, runbook, data card, notices), HANDOFF.md.

## Next actions (dispatch in parallel, real agent types)
0. Ask `git-workflow-master` for an initial local commit of the skeleton + contracts (the /goal prompt asks for git checkpoints; CLAUDE.md routes all git through that agent; local only, no remote).
1. `python-developer` (data): `src/gameqa/data/{prepare,manifest}.py`, `scripts/prepare_data.py`; HF revision sha; download only `data/test-00000-of-00001.parquet`; select visual-regression records by actual category string (~250 expected); map `media_folder` image/ vs repo `images/`; verify reference/candidate order; per-file download first 20 then the rest (cap ~3 GB); sha256 + dims; data/work/<id>/{reference,candidate}.png; seeded split demo(5)/dev(~10%)/eval(rest); `data/manifests/inference_manifest.json` (no labels) + `data/manifests/eval_labels.json`; `load_inference_manifest`, `load_eval_labels`, `rules_from_question`. Status: `docs/status/data-prep.md`.
2. `dl-engineer`: `src/gameqa/vision/{alignment,features,proposals,judge}.py` per D4; DINOv2 `dinov2_vits14` via torch.hub (check Python 3.13 compatibility; fallback transformers `facebook/dinov2-small`); Ollama `/api/chat` with base64 images + JSON-schema `format`, temperature 0; mock provider with fault injection (timeout / invalid_json / unknown_rule / forbidden / allowed); response validation; disk cache `data/cache/vlm/`; unit tests in `tests/vision/`; smoke artifacts `artifacts/dl_smoke/`; `docs/MODEL_NOTES.md`; status `docs/status/dl-engineer.md`.
3. `python-developer` (app): `pyproject.toml` + `pip install -e .` FIRST (so others can import `gameqa`), `app.py`, `src/gameqa/{pipeline,storage,cli,config,rules,report}.py`, `configs/rules_example.yaml` (brief section 6 A1/A2/D1/D2), `tests/app/` with Fake* stand-ins; artifacts layout per brief section 7; atomic writes; reference history; Streamlit session_state so reruns don't re-run inference; status `docs/status/python-developer-app.md`.
4. `qa-engineer`: `tests/conftest.py`, `tests/policy/test_decision.py` (exhaustive policy tests), synthetic fixtures `data/fixtures/<case>/` (identical, object_removed, lighting_change, clothing_color_change, allowed_and_forbidden, small_translation, different_dimensions, large_misalignment, small_object_removed, corrupt_upload, empty_rules, conflicting_rules) with `expected.json` incl. true bbox; `tests/acceptance/` (mock fault injection + `@pytest.mark.real_model` gated by `GAMEQA_REAL=1`); `scripts/evaluate.py` (predict without labels, then score; `--method classical` baseline); uses `code-reviewer`; `docs/QA_REPORT.md`, status `docs/status/qa-engineer.md`.
5. `experiment-tracker-pm`: `docs/EXPERIMENTS.md` (protocol + registry: E1 classical baseline vs E2 DINOv2+VLM on same eval IDs; E3 proposal recall on dev; E4 optional VLM-only), inference budget → recommended stratified eval subset size; `docs/DATA_CARD.md`, `THIRD_PARTY_NOTICES.md`; status file.
6. `documentation-engineer`: README.md, docs/CODE_WALKTHROUGH.md, docs/DEMO_RUNBOOK.md, docs/READABILITY_FEEDBACK.md, docs/HANDOFF_DRAFT.md (Azerbaijani + English terms; everything unverified marked UNVERIFIED); status file.

Each agent writes only its own files and its own `docs/status/<agent>.md`; senior-pm aggregates here.

## Milestone plan
0–1 h contracts + data inspection (contracts done) · 1–3 h runnable baseline + first real pairs · 3–6 h real DINOv2 + VLM + error states · 6–8 h eval + demos · 8 h+ freeze, fix, docs, handoff, git checkpoint.

## Owner decisions (before sleeping)
- VLM: stay with the light local model (`qwen2.5vl:3b` via Ollama) for this iteration. Do not ask for or wait on new API keys; the owner will revisit providers tomorrow.
- Git: commits allowed at any time, via `git-workflow-master`, local only (see CLAUDE.md).

## Open risks
- qwen2.5vl:3b quality/JSON compliance unknown; may need a larger local VLM (6 GB VRAM limit).
- torch.hub DINOv2 on Python 3.13 untested.
- Dataset media may be packed → smaller subset.
- No commits yet → no worktrees; enforce disjoint file ownership.

## Session 2 log
- Created `pyproject.toml` (setuptools, src layout, `gameqa` entry point, `real_model` pytest marker) and `pip install -e . --no-deps` → `import gameqa` works. Ownership handed to python-developer (APP).
- Wrote `docs/tasks/m1-tasklist.md` (ownership table, data + fixture contracts).
- Dispatched in parallel: git-workflow-master (initial commit), python-developer DATA, python-developer APP, dl-engineer, qa-engineer, experiment-tracker-pm, documentation-engineer. Each writes `docs/status/<name>.md`.
- If interrupted: read all `docs/status/*.md`, re-dispatch any workstream whose status file is missing or stale, then continue integration.
- Agent IDs (session 2, for SendMessage): DATA=afdb34c03018a7700, DL=a17dc2333c0a549cc, APP=acd79cea7f082b82b, QA=affe4eaa1acbfb700, EXP=a15e1832adce4ec82 (done), DOCS=a01bcf1c36e5f78de (done phase 1; re-dispatch once app/cli/artifacts exist).
- Done: initial commit d4b85af [was 9c09345]; D6 policy fixes (QA-D1/D2/D3); D7 splits + 60-pair eval subset; EXPERIMENTS.md, DATA_CARD.md (partial), THIRD_PARTY_NOTICES.md written.
- Checkpoint 3022ec8 [was 0b3cc1b]: integrated slice (101 files). Tests: 83 + 39 pass, 4 real_model skipped. APP done; real VLM run → NEEDS_REVIEW (audit timeout, rule-ID compliance) → sent to DL.
- D8: benchmark rules split into A1 (ACCEPTABLE) / D1 (UNACCEPTABLE); manifest regenerated. DATA done: 250 pairs, demo 5 / dev 40 / eval 205, eval_subset_60.json.
- QA done: 138 pass / 4 skip after D9. E1 classical: eval_full balanced acc 0.516 (bug recall 0.03) ≈ chance. E2/E4 blocked on real-VLM (D6 RAM, DL fixes).
- 58ba189 [was c463a07]: config frozen (D10). E2 (pipeline, 60) then E4 (vlm_only, 60) running serially in background → artifacts/eval/e2_pipeline_subset60, e4_vlm_only_subset60; logs artifacts/eval/e{2,4}_predict.log. Docs phase 2 re-dispatched (a8a27f55de610a06c).
- Docs phase 2 done (README, walkthrough, runbook, handoff draft, readability). Fixed now: decision.py docstring; approve of non-PASS/non-real run needs --force (CLI) / override checkbox (UI) + test → 164 pass / 6 skip.
- DEFERRED until E2+E4 finish (config/code frozen for eval): yaml `vlm.prompt_version` v1 vs real v9; judge.py fallback defaults ≠ yaml; SCENE_ID constant; mock-timeout reason text; judge.py dead code (`prep_crop`, identical branches, unused `_rule_fields` outputs); app engine cache keeps degraded after a load failure; then QA_REPORT/EXPERIMENTS/DATA_CARD refresh by owners.

## Session 3 (after power loss, 2026-10-09 morning)
- E2 60/60 complete; E4 resumed 50→60. Both scored. E1 re-tuned on final dev (D12). Verdict NOT SUPPORTED (D11/D12). Key false PASS: vr_bcbcf341.
- Real demo runs: object_removed FAIL, allowed_and_forbidden FAIL, small_object_removed FAIL, clothing_color_change PASS, lighting_change NEEDS_REVIEW, identical PASS; benchmark demo split 5/5 NEEDS_REVIEW (artifacts/demo/demo_split.jsonl).
- UI: Chrome extension not connected → scripts/ui_smoke.py (AppTest, real engines) OK: Analyze FAIL rendered, rerun no re-inference, approve v1+v2 + history.
- Commits: 871d8b1 [was 1f81dd2] (approve guard, docs phase 2). Post-eval cleanup (D11) uncommitted.
- Next: QA final acceptance + real_model tests; docs final; HANDOFF.md; fresh-process launch check; final commit.
- QA final verdict: accept as honest prototype, not a working detector. QA-D10/D11 fixed by senior-pm (D13), 168 passed / 6 skipped. Real-model tests 6 passed (QA, cached VLM).
- Fresh-process Streamlit launch: health ok / HTTP 200 (port 8517 check).
- HANDOFF.md written (Azerbaijani). Final commit via git-workflow-master.
- REMAINING (for Ali): real-browser UI click-through (Chrome extension was not connected); stronger VLM; review-rate reduction on dev; E2b; open minor QA-D12..D15.
