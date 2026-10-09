# Remaining tasks (Ali's side) — state at 2026-10-09 ~17:30 Baku

## Current checkpoint — overrides the historical 17:05 update below

- Celalın confirmed remote integration SHA-sı **`79a0ef740196cbaa0639579386c6c591d2bfd8ca`** fetch ilə təsdiqləndi. Frozen runtime: OpenRouter / `google/gemini-3.5-flash` / low / prompt v9; config `configs/openrouter_gemini_pilot.yaml`, C hash **`eaa371255716`**, B diagnostic hash `2dfeb64cd673` (namespace paths fərqli).
- C2 committed raw rows, 80 call/stage records və cost lokal olaraq yoxlanıb: [C2_VERIFICATION.md](C2_VERIFICATION.md), [C2_RECOMPUTED.json](C2_RECOMPUTED.json). B və C: **1 PASS /4 FAIL /7 REVIEW**, coverage **5/12**, bug false-PASS **1/5**, clean PASS **0/7**. C 3 bug FAIL +1 clean false-FAIL; B 2 bug FAIL +2 clean false-FAIL. Ümumi saylar eynidir; iki pair qərarı fərqlidir. B+C provider-reported toplam cost **$0.2871945**, retries 0.
- Exact frozen SHA-da offline tests **194 passed, 6 skipped**. 193/6 docs-branch nəticəsi və Celalın 186/6-deselected C2 nəticəsi ayrı checkpoint-lərdir.
- **Hazır:** updated pitch evidence, 113 s video shot list, 7-slide PDF/PPTX +3 science PNG. [SLIDE_HANDOFF.md](SLIDE_HANDOFF.md). 110 s silent motion draft [MOTION_HANDOFF.md](MOTION_HANDOFF.md)-də ayrıca izlənir; real UI recording deyil.
- **Gözlənir:** Celalın complete C2 evidence bundle-i (actual ZIP bytes/full captures) və **ayrıca UI-ready SHA**. Final recording həmin SHA gələnə qədər başlamır; Qwen branch UI istifadə edilmir. Code freeze SHA recording gate-i əvəz etmir.
- Local docs branch `docs/ali-next-session` unpublished-dir. Git-workflow-master onu confirmed frozen SHA üzərinə reconcile edir; push/PR agent tərəfindən edilmir, Ali ayrı terminalda explicit branch command işlədir.
- 17:30-dan sonra yalnız presentation/docs/verification/submission. Human video 18:45, acceptance 19:15, handoff 19:25, submission **19:30** dəyişmir. Optional second-rater və housekeeping prioritetdən çıxarılıb.

Historical base at session start: `feat/hackathon-demo-integration` @ `0826778`; superseded by confirmed `79a0ef7` above. Deadline: internal submission **19:30**, official **20:00** Baku. Rules from `/home/aliagabalayev/Downloads/02_ALI_CLAUDE_TODAY.md` still apply: **no new features, experiments or threshold tuning after 17:30.**

## Update 17:05 — Celal's C2 OpenRouter pilot (reported by Celal; not re-verified here)
- Gemini 3.5 Flash via **OpenRouter**, same dev12, same rules/policy, 80 fresh calls, 0 retries, reported cost **$0.2871945**; 186 tests passed; C evidence ZIPs verified (Celal).
- **Hybrid C: 1 PASS / 4 FAIL / 7 REVIEW** — coverage **5/12 (41.7%)**, bug false-PASS **1/5**.
- **Full-frame B: 1 PASS / 4 FAIL / 7 REVIEW** — coverage 5/12, bug false-PASS 1/5 (same counts as C).
- Barrel (vr_4b921c5d) and booth (vr_d07179d5) detected; **missing pedestal (vr_c1f47c57) wrongly PASS in both arms** → main documented failure.
- Framing: material improvement over Qwen's 0/12 coverage; B and C are equal on this set, so **no DINOv2-hybrid advantage is shown**.
- Celal's local C2 commit `e4a0cf3` is being reconciled with the remote integration branch (non-fast-forward after PR #3); he imports the `report.py` scope change from `3b794aa`. **Do not push or open PRs into `feat/hackathon-demo-integration` until Celal sends the reconciled SHA.** Ali's vision branch is frozen at `3591f7b`.
- Celal's instruction: use the **OpenRouter Gemini results as the final demo runtime evidence**; keep **Qwen A1/A3 as the baseline comparison**. Ali continues with video preparation and pitch-evidence cross-check.

Status legend: TODO / IN PROGRESS / BLOCKED. Owner: Ali = human; agent = Claude agent; Celal = teammate.

## A. Today, before submission (priority order)

| # | Task | Owner | Deadline | Inputs / notes | Done when |
|---|---|---|---|---|---|
| A1 | WAIT UI-ready SHA; record final 90–120 s video. 113 s shot list ready; 110 s motion evidence draft separately prepared | Ali (agent prepares) | 18:45 | C2 barrel `20261009T123704Z-8e4e19` FAIL; pedestal `20261009T124621Z-0b0c2b` false-PASS; Qwen REVIEW baseline. Final integration UI + exact config; labels every REPLAY / PRERECORDED / LIVE | Final video file exists; labels; ≤120 s; UI gate passed |
| A2 | DONE raw cross-check + pitch/video docs update. Pending actual ZIP bytes/full captures audit | agent + QA | 17:25 | `C2_RECOMPUTED.json`, `C2_VERIFICATION.md`, source SHA79a0ef7 | Raw counts/identities/cost recomputed; no unverified ZIP-byte claim |
| A3 | WAIT Celal C4 UI-ready SHA, launch command and browser export verification; then recording pre-flight | agent + Ali + Celal | before recording | No Streamlit listener was observed in this session's host process/port query; earlier :8501 inventory is historical. Final run bundle absent locally | Current UI opens exact runs; downloaded ZIP includes evidence.json |
| A4 | DONE 7-slide PDF/PPTX +3 evidence PNG + handoff; Celal assembles final deck | agent drafts, Celal assembles | 18:45 | `docs/ali/SLIDE_HANDOFF.md`, `pitch/`, `slides/` | Artifact files exist; numbers verified; team reviews |
| A5 | PARTIAL: counts/config/calls/cost/tests verified; actual final ZIP, second device, final video and human acceptance pending | qa agent + Ali + Celal | 19:15 | `docs/ali/A5_acceptance.md`, `C2_VERIFICATION.md` | Verdict with unmet items listed |
| A6 | Handoff checkpoint refreshed; add UI-ready SHA, final video path, submission confirmation when they exist | agent | 19:25 | `docs/ALI_HANDOFF.md` | Committed locally; Ali push/PR; final fields evidenced |
| A7 | Submission by authorized human; keep confirmation | Ali / Celal | 19:30 | package list (roadmap p.5) | Confirmation saved |

## B. Known defects / notes to hand to Celal (UI is Celal-owned; do not edit app.py/pipeline.py/decision.py/storage.py/contracts.py without him)
1. Loaded saved runs are not labelled "replay" in the UI.
2. After "Load saved run", the Rules editor shows the page's current rules, not the run's rules.
3. Typing into Approve → Reference ID reruns the page and collapses the expander (value kept).
4. evidence.json cache status stays "unknown (replay possible)" although Ali's input dump (`calls.jsonl`) proves fresh calls (QA-Q2). Fix would need per-call provenance in analysis.json (contract change → Celal).
5. Native DINOv2 identity prints `weights_sha256=unknown` under a custom TORCH_HOME (Celal's runtime).

## C. Housekeeping (low risk, any time before 19:00)
- DONE on docs/ali-next-session: `.gitignore` now ignores `data/cache_ali_*/` (setup file — Celal informed via PR).
- Delete local test reference `references/ui_check_ali/` (created by the UI check; git-ignored).
- Delete merged remote branches `docs/team-git-workflow`, `feat/hackathon-vision-evidence` (only when the user asks; pushes/deletes are blocked for agents — the user runs them).
- Optional: second-rater pass on `docs/ali/a1_evidence/obs_review.csv` (single rater, possible anchoring).

## D. After the hackathon (evidenced next steps, not today)
1. **Stronger VLM, same pipeline, same dev12 + eval60 IDs**: Gemini paid tier or another approved provider. Evidence: same-crop reproducer 2/2 (Ali) + fresh end-to-end barrel FAIL (Celal), both n≤2.
2. **E2b ablation**: classical-only proposals + VLM, to isolate DINOv2's contribution (never run).
3. **Global-change collapse**: 9/12 dev pairs (all cutscene) collapse → zero coverage. Calibrate `proposals.global_change_fraction` on dev only, or add a scoped "critical area" check (roadmap WP2 `scope_complete`). Re-measure false-PASS with coverage.
4. **Fresh held-out set**: independently collected, pre-labelled scene groups (dev12 labels are exposed to model outputs; eval60 is a historical regression set only).
5. **Per-call cache provenance in analysis.json** so reports can say live/mixed/replay truthfully.
