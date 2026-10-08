# AGENTS.md

Project agents for the **AI Gaming: Rule-Aware Visual Regression Prototype**. Definitions live in `.claude/agents/<name>.md`. Product context is in `docs/PROJECT_BRIEF.md`; every agent should read it before starting.

## Team

| Agent | Role | Owns | Reports to |
| --- | --- | --- | --- |
| `senior-pm` | Primary decision-maker: milestones, task lists, file ownership, integration, final acceptance | `docs/tasks/*-tasklist.md`, final `HANDOFF.md`, `docs/DECISIONS.md` | Product Owner (Ali) |
| `experiment-tracker-pm` | Experiment design, run tracking, statistical analysis for data/AI tasks | Experiment logs and results reports | `senior-pm` |
| `python-developer` | UI (Streamlit), contracts, orchestration, storage, dependencies | `app.py`, `src/gameqa/contracts.py`, `pipeline.py`, `storage.py`, `configs/` | `senior-pm` |
| `dl-engineer` | Alignment, DINOv2 features, region proposals, VLM adapter and prompt | `src/gameqa/vision/`, `docs/MODEL_NOTES.md` | `senior-pm` |
| `qa-engineer` | Independent tests, evaluation logic, acceptance evidence; uses `code-reviewer` for code review | `tests/`, `scripts/evaluate.py`, `docs/QA_REPORT.md` | `senior-pm` |
| `documentation-engineer` | README, code walkthrough, demo runbook, readability feedback, handoff narrative (Azerbaijani with English technical terms) | `README.md`, `docs/CODE_WALKTHROUGH.md`, `docs/DEMO_RUNBOOK.md` | `senior-pm` |

Supporting agents (not project-specific): `code-reviewer` (used by `qa-engineer`), `git-workflow-master` (all git operations).

### Gap: Data Engineer

The brief lists a **Data Engineer** (metadata preparation, media selection, manifest, `docs/DATA_CARD.md`, `src/gameqa/data/`), but no agent is defined for it yet. Until one is created, `senior-pm` assigns data preparation to `python-developer`.

## Delegation flow

1. `senior-pm` reads the brief, freezes contracts in the first hour, and writes the task list with an owner per task.
2. Plain implementation tasks go to `python-developer` or `dl-engineer` by ownership above.
3. Data/AI experiment tasks (model comparison, threshold or preprocessing trials, evaluation of the DINOv2 + VLM hypothesis) go to `experiment-tracker-pm`, which reports a recommendation back; `senior-pm` decides.
4. `qa-engineer` verifies independently and reviews code via `code-reviewer`; it gives `senior-pm` an acceptance verdict listing unmet criteria.
5. `documentation-engineer` documents only verified behavior and drafts the narrative of `HANDOFF.md`; `senior-pm` assembles and owns the final file.

## Working rules for all agents

- Only one owner edits a shared file at a time. Do not rewrite another agent's core logic; send suggestions to the owner.
- Mocks are always labelled and never presented as real DINOv2 / VLM inference. Distinguish "implemented", "loaded", "ran", and "measured".
- Held-out labels never enter prompts, tuning, or inference inputs.
- Never write credentials into code, reports, or logs; use environment variable names with placeholders.
- No training, fine-tuning, new paid providers, or new hardware.
- Box format is `[x1, y1, x2, y2]` in original reference pixel coordinates, right/bottom exclusive.
- No background processes in commands (never append `&`).
- Git: local only; all git operations go through `git-workflow-master`. See `CLAUDE.md`.
