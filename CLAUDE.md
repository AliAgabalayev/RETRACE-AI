# CLAUDE.md

## Project

**AI Gaming: Rule-Aware Visual Regression Prototype.** A local web app compares a reference game screenshot with a candidate screenshot under user-defined allow/deny rules. Flow: reference + candidate + rules -> DINOv2 change proposals -> per-region VLM verdict with visual evidence -> deterministic `PASS` / `FAIL` / `NEEDS REVIEW` -> bug report export or explicit "approve as new reference".

Full requirements: `docs/PROJECT_BRIEF.md` (read it before starting any task). Agent roster and ownership: `AGENTS.md`.

**Resuming work:** read `docs/status/senior-pm.md` (current state, done items, next actions) and `docs/DECISIONS.md` before doing anything else.

## Key facts from the brief

- **Hypothesis to test, not assume:** DINOv2 patch-feature proposals help a VLM do rule-aware comparison. No accuracy target and no claim of beating the paper.
- **Stack:** Python, Streamlit, PyTorch, OpenCV, Pillow, NumPy, Pydantic, pytest; one VLM client using existing credentials. One process, local files, small CLI. Proposed commands (`streamlit run app.py`, `python -m pytest`) are unverified until actually run.
- **Inference only:** frozen DINOv2 ViT-S/14 (`dinov2_vits14`), no training or fine-tuning, no new paid providers or hardware.
- **Out of scope:** video, game-playing agent, Unity/Unreal plugin, auth, cloud deployment, microservices, external issue trackers, automatic reference replacement.
- **Priorities:** P0 working end-to-end flow and handoff; P1 held-out smoke evaluation vs classical baseline, cache, diagnostics; P2 polish. P2 never delays P0.
- **Decision policy:** reliable forbidden change -> `FAIL`; all stages complete and only allowed changes -> `PASS`; uncertainty, rule conflict, unreliable alignment, model error, timeout, truncation -> `NEEDS REVIEW`. A component error never turns a proven `FAIL` into `PASS`.
- **Bounds:** max 8 regions + 1 whole-scene audit; 30 s request timeout, max 2 attempts; configurable end-to-end deadline.
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

- Git is used **locally only** for now. Do not add a remote, push, open PRs, or run any command that contacts a remote, unless the user explicitly asks.
- **All git operations (commits, branching, merging, rebasing, history cleanup) go through the `git-workflow-master` agent.** Do not run `git commit` or other history-changing commands directly; delegate them to that agent.
- Commits are allowed at any time without asking (checkpoints, finished tasks, integration points). They still go through `git-workflow-master` and stay local.
- Default branch is `master`.

## Project agents

Defined in `.claude/agents/`; roles, ownership and delegation flow are in `AGENTS.md`: `senior-pm`, `experiment-tracker-pm`, `python-developer`, `dl-engineer`, `documentation-engineer`, `qa-engineer`.
