# Git finalization — Ali docs → Celal integration → master

9 oktyabr 2026, Bakı. Bu audit zamanı fetched integration **`487f2028461b47013138be124ebf700b86a1c9f1`**, `master` **`b7aa8b8a2155cdbe2f71f9598fd25c3f50ed5683`**-dir. Integration `master`-dən **35 commit ahead**, 0 behind-dir. C4 readiness checkpoint `6850189`, C4 UI code `be1ea0a` və C2 raw verification source `79a0ef7` historical identity kimi saxlanılır; bunlar current integration HEAD deyil.

Ali-nin final docs/pitch branch-i **`docs/ali-final-pitch`**, worktree `/tmp/ali-final-pitch.pX8qSQ/checkout`-dur. Own unpublished branch latest fetched integration üzərinə conflict olmadan rebase edilib. Main checkout və işləyən `:8501` UI **`79a0ef7`**-də qorunub; orada yalnız dörd əvvəlki `data/cache_ali_*` untracked directory var. Credentials, caches, model weights, native artifacts və reference history stage/delete edilməyib. Yeni model/VLM job yoxdur.

## Branch audit

“Unique” həmin branch-də olub current integration-da olmayan commit sayıdır. Already-contained feature branches-i yenidən merge etməyə ehtiyac yoxdur.

| Branch / ref | Audited SHA | Unique | Action |
|---|---|---:|---|
| `origin/feat/hackathon-demo-integration` | `487f202` | 0 | Current integration / PR #4 head at fetch |
| local `feat/hackathon-demo-integration` | `79a0ef7` | 0 | Active UI checkout; 7 commits behind, switch edilməyib |
| local + remote `feat/hackathon-vision-evidence` | `74f84cf` | 0 | Already contained; PR #3 merged |
| local `feature/gemini-provider` | `08a0c3f` | 0 | Already contained |
| `origin/feat/hackathon-runtime-eval` | `7e7bb5d` | 0 | Already contained |
| `origin/docs/team-git-workflow` | `3fcab35` | 0 | Already contained; PR #1 merged |
| local + remote `master` | `b7aa8b8` | 0 | No direct commit/push; reviewed PR #4 target |
| `docs/ali-final-pitch` | Exact final HEAD in delivery message / PR | Final docs commits | One new PR into integration |
| `docs/ali-next-session` | `2d0140d` | 3 | Superseded docs; keep backup, no stale merge |
| `docs/ali-final-pitch-checkpoint` | `28f338b` | 4 | Keep backup |
| `docs/ali-final-pitch-pre-c4` | `15e9119` | 3 | Keep backup |
| `docs/ali-final-pitch-pre-deploy` | `1bb06ff` | 5 | Pre-rebase preservation checkpoint; keep backup |

`origin/HEAD` points to `origin/master`. PR #1 and #3 are MERGED; #2 is CLOSED. **Existing [PR #4](https://github.com/AliAgabalayev/neuroscience-hackhaton/pull/4) is OPEN: integration → master. Do not create a duplicate master PR.** At the `487f202` read it was MERGEABLE/UNSTABLE with no submitted reviews or review requests; prior `a6a8c8a` checks passed, latest-head checks still need confirmation. Mergeability/check status is time-dependent and must be read again after the docs merge.

## Review evidence and limits

Independent latest C5-composed Ali docs checkout suite: **199 passed, 6 skipped, 11.20 s**, exit 0. Actual command, run from `/tmp/ali-final-pitch.pX8qSQ/checkout`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/ali-final-pitch.pX8qSQ/checkout/src /home/aliagabalayev/Desktop/Workspace/neuroscience-hackhaton/.venv/bin/python -m pytest -q
```

`src/` diff to the exact C4 checkout, excluding `__pycache__`, and canonical config diff both exited 0. The C5 app delta is the missing-key Analyze guard and environment loading. Real-model skips are not passes. Independent exact C4 suite **197 passed, 6 skipped, 8.79 s**, pre-C5 composed docs suite **197 passed, 6 skipped, 9.67 s**, and Celal's Linux results are separate executions; they are not substituted for this local C5 composition result.

C5 compact `deploy/replay/barrel` package is now tracked, including sanitized historical four-call captures and source inputs. It is a replay seed, not fresh inference or the full twelve-run C2 ZIP bundle. Local Ali C5 browser/export reproduction and the complete C2 archive/input audit are separate acceptance work. The model/prompt/policy/canonical config hash **`eaa371255716`** and historical C2 measurements remain frozen.

Ali branch changes comprise verified pitch PNG/PDF/PPTX, evidence JSON/docs, local rendering scripts, and the original cache-ignore/resume-link housekeeping. Explicit paths are staged; `.env`, `data/`, `artifacts/`, `references/` are never added. Changed text/commit messages are checked for credential patterns and forbidden attribution trailers before push. No force-push or branch deletion is required.

## Two sequential reviewed PRs

Ali explicitly authorized opening the docs PR. The Git owner may attempt the explicit branch push and PR creation through the normal permission path. If the environment rejects that action, Ali runs these exact commands in a separate terminal. They work from the main repo without switching its active UI branch:

```bash
git fetch --prune origin
git push -u origin refs/heads/docs/ali-final-pitch:refs/heads/docs/ali-final-pitch
gh pr create --base feat/hackathon-demo-integration --head docs/ali-final-pitch --title 'docs: deliver verified Ali pitch and C2 handoff' --body-file /tmp/ali-final-pitch-pr-body.md
```

The prepared PR body is `/tmp/ali-final-pitch-pr-body.md`. These `/tmp` handoff files are local convenience files and are not part of the repository. If the docs PR already exists, view it rather than creating another one:

```bash
gh pr view docs/ali-final-pitch --json number,url,headRefOid,baseRefName,reviewDecision,reviews,statusCheckRollup
```

**Step 1:** Celal reviews the docs PR into `feat/hackathon-demo-integration`; Ali approves merge only after review and checks. The delivered exact docs HEAD must match the PR HEAD. Human merge command, with `FINAL_DOCS_SHA` replaced by the final delivery's full SHA:

```bash
gh pr merge docs/ali-final-pitch --merge --match-head-commit FINAL_DOCS_SHA
```

Do not use `--admin` or `--delete-branch`. No merge has been performed by this handoff task.

**Step 2:** Reuse PR #4 after Step 1. Its head changes when Ali docs enter integration; the earlier `487f202` HEAD is therefore not a valid final merge guard. Celal reviews the updated complete diff, latest checks and local acceptance limits. Read the new exact head and rerun/revalidate against it:

```bash
git fetch --prune origin
gh pr view 4 --json url,headRefOid,baseRefName,reviewDecision,reviews,mergeable,mergeStateStatus,statusCheckRollup
gh pr checks 4
```

`/tmp/ali-integration-master-pr-body.md` contains supplemental Ali review notes for the existing PR; this task does not edit Celal's PR description. Only after teammate review, latest-head checks and Ali's explicit merge approval may the human use:

```bash
gh pr merge 4 --merge --match-head-commit UPDATED_REVIEWED_INTEGRATION_SHA
```

Merge commits preserve the freeze/source ancestry used by the evidence. After merge, verify PR #4 state/merge commit and fetch `origin/master`; report actual final SHA then. Direct `master` push, forced history changes, automatic integration/backup deletion and unreviewed merge are outside these steps.

## Evidence outside Git

`artifacts/ali/motion/ali_evidence_motion_DRAFT_110s.mp4` is a **110 s silent PRERECORDED/DRAFT evidence walkthrough**, SHA256 **`cda409954b356249d71c37d92cc4fdf9a0a7c39f8228fb19a9db6b9033dee228`**. It is git-ignored and **is not backed up by a branch push or PR**. Preserve/copy it through the agreed artifact handoff; do not claim the MP4 is committed. Source slides and renderer are tracked. Final UI recording, narration, second-device acceptance and submission confirmation remain pending; internal submission deadline **19:30**.
