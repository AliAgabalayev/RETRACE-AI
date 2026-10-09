# CLAUDE.md

## Project

**AI Gaming: Rule-Aware Visual Regression Prototype.** A local web app compares a reference game screenshot with a candidate screenshot under user-defined allow/deny rules. Flow: reference + candidate + rules -> DINOv2 change proposals -> per-region VLM verdict with visual evidence -> deterministic `PASS` / `FAIL` / `NEEDS REVIEW` -> bug report export or explicit "approve as new reference".

Full requirements: `docs/PROJECT_BRIEF.md` (read it before starting any task). Agent roster and ownership: `AGENTS.md`.

**Resuming work:** read `HANDOFF.md` (current state, results, next tasks), `docs/status/senior-pm.md` and `docs/DECISIONS.md` (D1–D14) before doing anything else.

## Key facts from the brief

- **Hypothesis to test, not assume:** DINOv2 patch-feature proposals help a VLM do rule-aware comparison. No accuracy target and no claim of beating the paper.
- **Stack:** Python, Streamlit, PyTorch, OpenCV, Pillow, NumPy, Pydantic, pytest. One process, local files, small CLI. Always use `.venv/bin/python` / `.venv/bin/streamlit`. Verified: `.venv/bin/streamlit run app.py`, `.venv/bin/python -m pytest -q`.
- **VLM providers (D10, D14):** default is local Ollama `qwen2.5vl:3b` (runs on CPU, needs ~9 GB free RAM; run one VLM job at a time). Optional OpenAI-compatible API (`configs/openai.yaml`, `configs/openrouter.yaml`) selected via `GAMEQA_CONFIG` or CLI `--config`; keys live only in the git-ignored `.env` (template `.env.example`). Never print, log or commit key values.
- **Inference only:** frozen DINOv2 ViT-S/14 (`dinov2_vits14`), no training or fine-tuning, no new hardware. Paid APIs only as the owner-approved optional OpenAI-compatible VLM (D14).
- **Out of scope:** video, game-playing agent, Unity/Unreal plugin, auth, cloud deployment, microservices, external issue trackers, automatic reference replacement.
- **Priorities:** P0 working end-to-end flow and handoff; P1 held-out smoke evaluation vs classical baseline, cache, diagnostics; P2 polish. P2 never delays P0.
- **Decision policy:** reliable forbidden change -> `FAIL`; all stages complete and only allowed changes -> `PASS`; uncertainty, rule conflict, unreliable alignment, model error, timeout, truncation -> `NEEDS REVIEW`. A component error never turns a proven `FAIL` into `PASS`.
- **Bounds:** max 8 regions + 1 whole-scene audit; request timeout 75 s for the CPU-resident Qwen (brief default 30 s, changed in D10; 60 s in the API configs), max 2 attempts; configurable end-to-end deadline.
- **Box format:** `[x1, y1, x2, y2]` in original reference pixel coordinates, right/bottom exclusive.
- **Data:** VideoGameQA-Bench (CC BY 4.0), visual-regression subset (~250 samples). Metadata-first; download only selected images, never the full 33.4 GB repository. Labels live only in an evaluation-only manifest and never reach inference. Verify actual schema, counts and paths; do not guess.
- **Honesty:** mocks are always labelled and never shown as real inference. Degraded modes are reported as degraded, not as "full AI prototype complete".
- **Language:** `HANDOFF.md` and documentation for Ali are in Azerbaijani with English technical terms.
- **Decisions:** record any change to the brief's defaults in `docs/DECISIONS.md`.

## Docs layout

- `docs/PROJECT_BRIEF.md`: project brief (source of truth for scope).
- `docs/tasks/`: task lists written by `senior-pm`.
- `docs/DECISIONS.md`, `docs/MODEL_NOTES.md`, `docs/QA_REPORT.md`, `docs/DATA_CARD.md`, `docs/CODE_WALKTHROUGH.md`, `docs/DEMO_RUNBOOK.md`, `HANDOFF.md`: created by the owning agents during the build (see `AGENTS.md`).

## Git rules

- Remote: `origin` = private GitHub repo https://github.com/AliAgabalayev/neuroscience-hackhaton (branch `master`). **Push, open PRs, or change repo settings only when the user explicitly asks.** Never force-push.
- Before any push, scan the commits being pushed for secrets; `.env`, `data/raw`, `data/work`, `data/cache`, `artifacts/`, `references/` must never be committed.
- **All git operations (commits, branching, merging, rebasing, history cleanup) go through the `git-workflow-master` agent.** Do not run `git commit` or other history-changing commands directly; delegate them to that agent.
- Local commits are allowed at any time without asking (checkpoints, finished tasks, integration points). They still go through `git-workflow-master`; pushing them still needs an explicit request.
- Default branch is `master`.

## Project agents

Defined in `.claude/agents/`; roles, ownership and delegation flow are in `AGENTS.md`: `senior-pm`, `experiment-tracker-pm`, `python-developer`, `dl-engineer`, `documentation-engineer`, `qa-engineer`.
