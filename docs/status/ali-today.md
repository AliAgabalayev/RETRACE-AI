# Ali today: status board (2026-10-09, Baku)

Written ~16:00 by senior-pm. Source of requirements: `/home/aliagabalayev/Downloads/02_ALI_CLAUDE_TODAY.md`. Branch `feat/hackathon-vision-evidence`, HEAD `a5590a5` (on origin). Integration branch (Celal): `feat/hackathon-demo-integration` (`0e234d8` wires `storage.export_report`).

## 1. Milestones

| ID | Window | State | Evidence |
|---|---|---|---|
| A0 inputs, labels, runtime | 14:30-15:15 | done | `docs/ali/A0_status_for_celal.md`, `docs/ali/runtime_inventory.md`, `configs/ali_dev12.json` (cf861f1), `docs/ali/labels_ali.csv` frozen e844aab, `docs/ali/labels_audit.md` (post-freeze, labels file untouched) |
| A1 perception diagnostic | 15:15-15:45 | done | `docs/ali/A1_diagnostic.md`, `docs/ali/a1_evidence/` (predictions_{A,B,C}.jsonl, score_raw.md, stage1_qwen_vs_gemini.json), D17 in `docs/DECISIONS.md` (freeze Qwen build; agreed by Celal) |
| A2 evidence workflow | 15:45-16:35 | mostly done, 2 verifications open | `src/gameqa/report.py` evidence sidecar (667925f), `docs/ali/evidence_shape.md`, demo ZIPs in `artifacts/ali/demo_zips/` (vr_4b921c5d, vr_09a066d3, vr_330651ed; all NEEDS_REVIEW), Celal hook `0e234d8`. Vision fix: intentionally none (D17) |
| A3 frozen comparison + visual review | 16:50-17:30 | in progress | Fresh run on Ali host, `configs/ali_a3_qwen.yaml` (same as `ali_a1_qwen.yaml` except cache namespace `data/cache_ali_a3` and dump tag), outputs `artifacts/ali/a3/`, ETA ~16:25. Scoring and review not started |
| A4 demo, video, pitch | 17:30-18:45 | prep done, recording todo | `docs/ali/DEMO_VIDEO_NOTES.md`, `docs/ali/PITCH_EVIDENCE.md`; both are A1-based and must be rechecked against A3 |
| A5 acceptance + submission | 18:45-19:30 | todo | none yet |

## 2. Gap check (every A2-A5 bullet)

Legend: MET / PARTIAL / UNMET / N/A. Deadlines are today.

### A2
| Bullet | Status | Gap, owner, deadline |
|---|---|---|
| One small configurable vision fix if perception chosen | N/A | D17 chose freeze; model change is documented as next step, not run (Gemini 20 req/day) |
| Celal coverage change, vision fixed | N/A | not selected; confirm with Celal that nothing changed in policy since A1 (Ali, 16:10) |
| Report has IDs/hashes, expected vs observed, rule IDs, crops, scope, decision+reasons, model/prompt/config identity, unassessed areas | PARTIAL | Sidecar built; not yet proven in a ZIP produced by the normal export path (`0e234d8`). qa-engineer unzips and ticks each field by 16:20 |
| Reuse current ZIP exporter, check real ZIP for input/crop/JSON/Markdown | PARTIAL | Demo ZIPs were built with bridge script. Check on both bridge ZIPs and a ZIP from Celal's exporter. qa-engineer, 16:20 |
| Honest cache provenance | MET | Report says "unknown (replay possible)"; A1/A3 use fresh namespaces with per-call provenance in `calls.jsonl`. No exact cache percentages to be claimed |
| Focused tests for change and report evidence; timeout/error/unknown rule stays REVIEW | PARTIAL | `tests/vision/test_report_evidence.py` exists. Strict xfail `test_plain_export_report_writes_evidence` will XPASS-fail once Celal's hook is merged: marker must be removed. python-developer, 16:30, coordinated with Celal (marker removal on whichever branch has the hook). Run `python -m pytest tests/vision` and paste output |
| Send Celal one real analysis.json + ZIP early | PARTIAL | ZIPs exist; Ali confirms Celal has them (message, Ali, 16:10) |
| 16:35 push tested branch with SHA, files, commands, tests/skips, config, results, problems; no merge to master | PARTIAL | Code is on origin at a5590a5. Remaining: commit `configs/ali_a3_qwen.yaml` and any test fix, Ali pushes by hand, handoff note lists SHA and unresolved problems (git-workflow-master commit 16:30, Ali push 16:35) |

### A3
| Bullet | Status | Gap, owner, deadline |
|---|---|---|
| Run frozen build, single runner, no concurrent load | IN PROGRESS | Ali host. Nobody starts another Ollama/VLM job or the Streamlit live run until it ends (~16:25) |
| B and C same model/provider/rules/aligned input; pixel control | PARTIAL | Config identity is by construction; experiment-tracker-pm verifies in the A3 predictions (model, prompt version, rules hash, input hashes), 16:50 |
| Check errors, duplicates, missing IDs, cached/fresh; keep REVIEW cases | UNMET | experiment-tracker-pm, 16:50 |
| Dev12 = development diagnostic; 60 eval = historical regression; fresh holdout optional | PARTIAL | Wording exists in A1 doc; A3 review doc must repeat it. Fresh holdout: cut (not a blocker) |
| Keep at least one genuine failure/boundary example with evidence | MET (A1 basis) | vr_4b921c5d with crop and Gemini reproducer. Re-confirm it still holds in A3 (qa-engineer, 17:10) |
| If hybrid does not improve useful decisions, support simpler method; no DINOv2 superiority claim | PARTIAL | A1 reading: A and B pass all 5 bugs (unsafe), C safe but 0/12 coverage. Decide wording after A3 numbers: no superiority claim, state trade-off plainly. senior-pm decision at 17:15 |
| Celal owns scoring, Ali owns visual checks | PARTIAL | Celal's scoring scripts run read-only by experiment-tracker-pm; Celal cross-checks numbers by 17:20 |
| Extra gap (not in assignment but promised): observation accuracy (target 10/12) | UNMET | `obs_review.csv` unmarked. Ali marks 12 rows during the A3 wait (16:05-16:25, about 10 min); if not marked by 17:15, report "not scored" |

### A4
| Bullet | Status | Gap, owner, deadline |
|---|---|---|
| No new features/experiments/tuning after 17:30 | rule | enforced, see stopping rules |
| 90-120 s video: problem; real bug with crop/rule; allowed PASS if achieved; honest REVIEW; ZIP export; brief comparison | PARTIAL | Shot list exists. Allowed PASS from hybrid was NOT achieved in A1 (0/7); show it as a missing case, not a result. Bug shot is REVIEW, not FAIL (re-verify with A3). Ali records 17:30-18:30 |
| Mark cached/prerecorded segments; measure live wall time separately; visible cuts | PARTIAL | Labels defined in notes. Live timing unmeasured: Ali measures 18:30-18:45 with no other load, n stated |
| Pitch technical evidence (DINOv2 role, VLM role, code decides, counts, missing cases, failure, next pilot) | PARTIAL | `PITCH_EVIDENCE.md` is complete on A1 numbers. documentation-engineer refreshes to A3 by 17:25; qa-engineer verifies numbers vs raw rows by 17:25 |
| Banned claims (fine-tuned, production-ready, QA workload reduced) | MET | listed in both docs; qa-engineer greps at A5 |
| Ali records; Celal assembles slides | MET (assignment) | Ali delivers video + 3 slide images (A1 table, Qwen vs Gemini, failure) to Celal by 18:45 |
| Optional usability exercise | CUT | cut first per priority order |

### A5
| Bullet | Status | Gap, owner, deadline |
|---|---|---|
| Open actual demo URL from another device; test upload/decision/download if claimed | UNMET / UNKNOWN | Deployment is Celal's; Ali asks Celal by 17:00 whether a URL exists. If none: replay/video only, say exactly that. qa-engineer tests, 19:00 |
| Unzip evidence report | PARTIAL | first pass 16:20; final pass on the exact ZIP in the package, 19:00 |
| Check Celal's pitch numbers vs raw rows and denominators | UNMET | qa-engineer, 19:05 (earlier pass on Ali's numbers at 17:25) |
| Package: code commit, launch command, model/config identities, input provenance, raw predictions, metrics, ZIP, video, pitch, limitations | UNMET | qa-engineer checklist 19:10; Ali + Celal review 19:20 |
| Authorized human submits by 19:30, keeps confirmation | UNMET | Ali (or Celal) submits; no external messages by agents |

## 3. Remaining task list

| # | Task | Owner | Deliverable | Deadline | Depends on |
|---|---|---|---|---|---|
| 1 | Mark observation correctness for dev12 | Ali | `docs/ali/a1_evidence/obs_review.csv` filled (or "not scored") | 16:25 | none (do while A3 runs) |
| 2 | Report/ZIP field verification on 3 demo ZIPs + one Celal-exporter ZIP | qa-engineer | `docs/ali/A5_acceptance.md` section "ZIP check" with unzip -l output and field-by-field ticks | 16:20 | none |
| 3 | Test marker fix and tests green | python-developer | xfail marker removed once hook is on the branch under test; `python -m pytest tests/vision` output pasted | 16:30 | task 2, Celal hook 0e234d8 |
| 4 | Commit `configs/ali_a3_qwen.yaml` (not caches) and test fix; local only | git-workflow-master | commit SHA, `git status` clean except caches | 16:30 | 3 |
| 5 | Push, open PR as draft, report SHA | Ali (by hand) | origin SHA, draft PR | 16:35 | 4 |
| 6 | A3 scoring (A/B/C on 12), integrity checks (errors, duplicates, missing IDs, cache namespace, model/prompt identity) | experiment-tracker-pm | `artifacts/ali/a3/score_raw.md`, integrity table | 16:50 | A3 run finishes ~16:25; Celal scripts read-only |
| 7 | A1 vs A3 determinism comparison (per-pair decision, region count, observation text) | experiment-tracker-pm | section in `docs/ali/A3_review.md` | 16:55 | 6 |
| 8 | A3 review doc: counts vs targets, failure example, wording rules, go/no-go recommendation | experiment-tracker-pm | `docs/ali/A3_review.md` | 17:10 | 6, 7, 9 |
| 9 | QA visual review of A3: VLM-input crops for 3 demo pairs and every changed verdict vs A1; failure example preserved | qa-engineer | `docs/ali/A3_visual_review.md` with image refs | 17:10 | A3 run |
| 10 | PM decision on pitch/demo wording after A3 | senior-pm | decision line appended to `docs/DECISIONS.md` (D18) only if numbers differ from A1 | 17:15 | 8, 9 |
| 11 | Pitch number verification against raw rows (denominators) | qa-engineer | verification table in `docs/ali/A5_acceptance.md` | 17:25 | 6, 10 |
| 12 | Refresh PITCH_EVIDENCE, DEMO_VIDEO_NOTES, ALI_HANDOFF to A3 numbers (Azerbaijani + English terms for handoff) | documentation-engineer | updated three docs; every changed number cites its raw file | 17:25 | 8, 10, 11 |
| 13 | Commit docs, mark PR ready for review | git-workflow-master, then Ali | commit SHA; PR ready | 17:30 (if A3 raw outputs are complete; see risk R1) | 12 |
| 14 | Ask Celal: deployment URL exists? final slide format? | Ali | answer recorded in this file | 17:00 | none |
| 15 | Video prep: stop all other VLM jobs, Ollama up, Streamlit launch tested, saved runs load, ZIP unzipped on screen verified | Ali | rehearsal done | 17:30 | A3 finished |
| 16 | Record 90-120 s video, labels REPLAY/PRERECORDED/LIVE | Ali | video file | 18:30 | 12, 15 |
| 17 | Live wall-time measurement, new empty cache, no other load, n stated | Ali | numbers in video notes | 18:45 | 16 |
| 18 | Deliver video + 3 slide images to Celal | Ali | files handed over | 18:45 | 16 |
| 19 | A5 acceptance: other-device test (only what exists), unzip final ZIP, package checklist, banned-phrase grep | qa-engineer | `docs/ali/A5_acceptance.md` verdict with unmet items listed | 19:10 | 18, Celal package |
| 20 | Joint review Ali + Celal, submit, keep confirmation | Ali, Celal | confirmation saved | 19:30 | 19 |

## 4. Stopping rules

- **16:35**: stop quality patching. Only fixes to a broken test or a wrong document claim remain allowed; no vision, prompt, threshold or policy edit. If a patch fails acceptance, revert to the frozen baseline.
- **17:30**: no experiments, no new features, no threshold tuning, no new model runs. Only the live wall-time measurement (task 17) is allowed afterwards, as a measurement, after recording.
- **19:30**: submission by the authorized human; deadline is 20:00. If a milestone is already late, cut optional work (cut order: usability exercise, oracle/second-model work, fresh holdout), never the 17:30 or 19:30 gates.
- Standing: one VLM job at a time on Ali's host (lock `artifacts/ali/vlm.lock`); agents do not push; labels file `docs/ali/labels_ali.csv` is never edited; no mock shown as inference; unresolved failures never become PASS.

## 5. Open risks

- **R1: A3 not finished by 16:35.** Mitigation: push code at 16:35 regardless (code is frozen); keep PR draft; mark ready only when A3 raw outputs are complete and scored, hard limit 17:15. If A3 fails/crashes, fall back to A1 raw rows as the evidenced numbers, label the missing fresh run explicitly.
- **R2: A3 differs from A1 (Ollama non-determinism).** Demo/pitch currently say vr_4b921c5d is REVIEW and C is 12/12 REVIEW. Any difference must be reported as is (A1 and A3 both shown); the "do not say FAIL" rule is re-evaluated against A3; never pick the better run.
- **R3: Pitch lacks a positive result.** No allowed PASS and no FAIL from the hybrid; framing must stay "localization works, perception (VLM) is the bottleneck; abstention is safe but coverage is 0". No superiority claim. Not to be patched after 16:35.
- **R4: Label weaknesses.** 5 rows were Claude-proposed and confirmed by Ali, frozen after first outputs; vr_330651ed is ambiguous (sensitivity table in `labels_audit.md`). Must stay in limitations.
- **R5: Observation accuracy unscored** unless Ali completes task 1.
- **R6: Evidence sidecar not proven through the normal export path**; strict xfail will break tests after merge with the hook; bridge script `scripts/ali_export_evidence.py` was never run by the doc author.
- **R7: Deployment unknown.** If no URL, A5 only verifies video/replay; claim exactly that.
- **R8: CPU contention.** Live Streamlit/Ollama use during A3 would slow or corrupt timing and break the single-runner rule. Wall times from A1 (B 38-48 s, C 69-160 s) are CPU values.
- **R9: Quota.** Gemini 20 req/day/model already partly used; no reruns on camera.
- **R10: Untracked caches** (`data/cache_ali_*`) must not be committed.
