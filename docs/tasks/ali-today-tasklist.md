# Ali today (2026-10-09, Baku) - Task List

## Specification Summary
**Authoritative source**: `/home/aliagabalayev/Downloads/02_ALI_CLAUDE_TODAY.md` (A0-A5). Quotes: "Your branch: `feat/hackathon-vision-evidence`", "Target all 6 clean and seeded 6 bug pairs, ideally 3 Unity + 3 cutscene, chosen before model results", "Freeze labels before seeing model outputs", "Only ONE VLM job at a time", "At 16:35 stop quality patching", "No new features, model experiments or threshold tuning after 17:30".
**Stack**: Python, Streamlit, frozen DINOv2 ViT-S/14 (CUDA, RTX 3060 6 GB), existing VLM adapters in `src/gameqa/vision/judge.py`.
**Timeline**: A0 14:30-15:15 | A1 15:15-15:45 | A2 15:45-16:35 | freeze 16:50 | A3 16:50-17:30 | A4 17:30-18:45 | A5 18:45-19:30 | submit 19:30, deadline 20:00.
**Frozen, must not change**: manifest sha256 prefixes inference_manifest `245815f5191e6708`, eval_labels `a10ab8dd2f936ada`, eval_subset_60 `ff765d14428cd944`. Never run `prepare_data.py` (it rebuilds manifests).

## Decisions (PM, final)
- (a) **Branch**: create `feat/hackathon-vision-evidence` FROM `feature/gemini-provider` (08a0c3f), which is exactly one commit above shared base `b7aa8b8`. Why: the judge.py fixes (reasoning_effort, cache-key fix, 429/503 backoff) are in Ali-owned files, are needed to get any Gemini run to work, and sit on the audited base so Celal's diff stays tiny. Tell Celal the base is `b7aa8b8` + 1 commit `08a0c3f` (touches judge.py, tests/vision/test_openai_provider.py, configs/gemini.yaml, scripts/list_models.py, .env.example, docs/DECISIONS.md D16). Do not merge to master. If Celal refuses the extra commit, cherry-pick it onto a branch from `b7aa8b8`.
- (b) **Inference host**: one host, the Ali machine, one VLM job at a time (lock file `artifacts/ali/vlm.lock`). Order of preference at the 14:55 probe:
  1. Local Ollama `qwen2.5vl:3b` if free RAM >= 9 GB after closing apps (browsers, IDEs). Also try `OLLAMA_NUM_PARALLEL=1`, smaller `num_ctx`. Budget: ~70 s/pair, so B full-frame x12 ~ 15 min; hybrid is several calls per pair, so A1 runs on the **predeclared balanced six** (3 clean + 3 bug) first, remaining six only if time allows.
  2. Else Gemini `gemini-3.5-flash` (one probe call only; 20/day cap shared). Spend the quota ONLY on: B full-frame x12 (12 calls) + at most 8 hybrid calls on the six. No retries beyond backoff, no ad-hoc tests.
  3. Else (neither works at 15:15): environment recovery has priority per assignment; use the Gemini fixture FAIL already obtained as the "one real response" artifact, report A1 as not measured. Never invent a baseline; never use mocks as inference (label them).
  Record provider/model id, RAM observation, request duration for one real response at A0 (A0.8).
- (c) **12 dev IDs**: seeded script `scripts/ali_select_dev12.py` (seed `20261009`, `random.Random(seed)` over IDs sorted lexicographically). Selection = all 6 clean + 3 Unity bug + 3 cutscene bug sampled without replacement. Reads only the dev-split ID list and the family/source field (needed for stratification) - never any model output. Writes `configs/ali_dev12.json` (ids, seed, counts, input manifest hash) and is committed BEFORE any model call; commit time is the proof. Balanced-six fallback (predeclared, same file): the first 3 clean + first 3 bug by seeded order, 2 Unity + 1 cutscene... exact: 3 clean, 2 Unity, 1 cutscene. Fixed now, not after seeing results.
- (d) **Labels are Ali's**. Agents produce `docs/ali/labeling_sheet.csv` (empty label columns) and `docs/ali/contact_sheet_*.png`; they must not fill any label, bbox or rule field, and must not read `labels_ali.csv` content into any prompt. Labels live in `docs/ali/labels_ali.csv` (separate file, frozen by Ali with a git commit before A1 starts).
- (e) **Cut order if short** (first cut first): 1) A5 usability exercise and brief comparison view in video; 2) second model / oracle-bbox diagnostic; 3) remaining-six hybrid run (fall back to the balanced six); 4) per-stage cache provenance (use fresh namespace + "replay/unknown" wording); 5) vision fix in A2 (keep baseline; spend block on evidence/report); 6) DINOv2-superiority claim (report honestly instead). NEVER cut: A0 inputs/labels, report ZIP with evidence, honest REVIEW/failure example, video.

## Work packages

### [ ] WP0.1: Git setup and base verification
**Owner**: git-workflow-master. **Deadline**: 14:50 (A0).
**May write**: git metadata only (local branch `feat/hackathon-vision-evidence` from `feature/gemini-provider`). No remote, no push unless Ali explicitly asks.
**Acceptance**: `git rev-parse HEAD` = 08a0c3f, `git merge-base HEAD origin/master` = b7aa8b8, working tree clean, three manifest sha256 prefixes unchanged (print them).
**Dependencies**: none.

### [ ] WP0.2: Dev12 selection script
**Owner**: python-developer (instance 1). **Deadline**: 15:00.
**May write**: `scripts/ali_select_dev12.py`, `configs/ali_dev12.json`, `tests/vision/test_ali_select.py`.
**Inputs**: `data/manifests/*.json` (read-only), dev split list.
**Deliverable**: deterministic selection per decision (c) incl. balanced-six fallback and clean-count assertion (6 clean, else record actual counts and stop, no fill from eval).
**Acceptance**: two runs produce byte-identical json; counts 6 clean/3 Unity/3 cutscene (or actual counts recorded); no label/verdict field beyond family and clean/bug used; unit test passes; manifest hashes unchanged.
**Dependencies**: WP0.1. Commit via git-workflow-master BEFORE WP1.x.

### [ ] WP0.3: Selective asset bundle and hash inventory
**Owner**: python-developer (instance 2). **Deadline**: 15:05.
**May write**: `scripts/ali_bundle_assets.py` (new), `artifacts/ali/bundle/` (copy of 12 pairs), `artifacts/ali/inventory.json`.
**Deliverable**: for the 12 IDs: both image paths, decoded dimensions, sha256, dataset source/revision from manifest. Images are already under `data/work/<id>/`; copy only, no download, no `prepare_data.py`.
**Acceptance**: inventory has 24 image rows with sha256 and w x h; script re-run yields same hashes; Celal can run from the bundle without any download.
**Dependencies**: WP0.2.

### [ ] WP0.4: Labeling sheet and contact sheets (no labels)
**Owner**: python-developer (instance 2, after WP0.3). **Deadline**: 15:05 (Ali labels 15:05-15:25, overrunning A0 by 10 min is accepted; labels frozen before A1 start at 15:25 if time-boxed, otherwise Ali labels 6-case balanced set first).
**May write**: `scripts/ali_make_sheets.py`, `docs/ali/labeling_sheet.csv`, `docs/ali/contact_sheet_<id>.png` (before | after | abs-diff, same scale, IDs only).
**Columns (all empty)**: id, visible_primary_change, valid_comparison_conditions, source_scene, rule_allowed_or_forbidden, approx_bbox_x1y1x2y2_reference_px, uncertainty, out_of_scope(Y/N).
**Acceptance**: sheet has 12 rows, all label columns empty; no model output used; images readable at Ali's screen size.
**Dependencies**: WP0.3.

### [ ] WP0.5: Runtime inventory and one real response
**Owner**: dl-engineer. **Deadline**: 15:10.
**May write**: `docs/ali/runtime_inventory.md`, `artifacts/ali/first_response/*`.
**Deliverable**: the 14:55 host probe (decision b): free RAM, Ollama model load success/failure, one Gemini probe only if Ollama impossible; ONE real request on one of the 12 pairs via existing `judge.py` with duration, provider/model id, saved prompt images and raw JSON. No credentials printed.
**Acceptance**: file lists chosen host, fallback status, RAM, duration; response artifact present and labelled real; or an explicit "no working path" note triggering recovery.
**Dependencies**: WP0.2 committed (so the pair is a dev12 member).

### [ ] WP0.6: Inventory message to Celal
**Owner**: documentation-engineer. **Deadline**: 15:15.
**May write**: `docs/ali/A0_status_for_celal.md`.
**Deliverable**: factual summary: base SHA chain, ID list, bundle hash inventory, host/model/latency, lock rule (Ali runs VLM jobs), manifest hashes, open blockers. Report format: completed / evidence / blocker / next. English technical terms; no secrets.
**Dependencies**: WP0.1-0.5; Ali sends it himself.

### [ ] WP1.1: Perception diagnostic runs (full-frame vs region)
**Owner**: experiment-tracker-pm. **Deadline**: 15:40 (A1).
**May write**: `docs/ali/A1_diagnostic.md`, `artifacts/ali/a1/**`, `configs/ali_a1.yaml`.
**Design**: same VLM/provider/rules for arms B (full-frame) and C (automatic DINOv2 regions); optional separate "oracle" arm using Ali's bboxes (label it oracle, never mixed into C); pixel diff as non-semantic control. Run the balanced six first, then remaining six if time. Save exact images/composites the VLM sees (with resize 336/512 note). One run at a time (lock file). Fresh cache namespace `ali_a1`.
**Scoring (after labels frozen)**: stage-1 observation correct vs checklist (Ali judges borderline; agent proposes), plus per-case buckets: wrong perception / wrong rule mapping / missing proposal / policy abstention; truncation split into global-change vs max-region cap. Report actual counts vs targets (10/12 observations, 0/6 bug false-PASS, >= 4/6 clean PASS, coverage >= 6/12) including failed targets.
**Acceptance**: run table with 12 (or 6) IDs, no missing/duplicate IDs, cached/fresh flag, errors kept; recommendation of exactly ONE intervention with reproducer command, delivered to senior-pm by 15:45.
**Dependencies**: WP0.5, Ali's frozen labels, Celal's runner (use `scripts/evaluate.py` read-only; if its interface is not ready, run via `gameqa` CLI/pipeline read-only).

### [ ] WP1.2: Crop/resize inspection
**Owner**: dl-engineer. **Deadline**: 15:40.
**May write**: `docs/ali/A1_crops.md`, `artifacts/ali/a1_crops/**`.
**Deliverable**: visual inspection of saved VLM inputs: thin crops, 336/512 resizing, overlaid captions; annotate where detail is lost with image evidence. Parallel to WP1.1 but read-only on its outputs (no VLM calls).
**Acceptance**: per pair verdict "detail preserved / lost" with file refs; feeds the single recommendation.
**Dependencies**: WP1.1 artifacts (starts as soon as first ones exist).

### [ ] WP2.1: Chosen vision fix (only one)
**Owner**: python-developer (instance 1) with dl-engineer review. **Deadline**: 16:30.
**May write**: `src/gameqa/vision/judge.py`, `prompts.py`, `proposals.py`, `features.py` (only if the fix requires it), `configs/ali_*.yaml`, `tests/vision/*`.
**Gate**: PM selects at 15:45 among model/provider change, crop representation (config flag, default off), or Celal-owned coverage change. If Celal's coverage change is chosen, this WP is replaced by WP2.2 only and vision code stays fixed.
**Acceptance**: one config-gated change; paired scale and before/after correspondence preserved; boxes stay original reference pixels `[x1,y1,x2,y2]` exclusive; timeout/error/unknown rule still NEEDS REVIEW; `python -m pytest tests/vision` passes (output pasted); same 12 re-measured and compared to A1 baseline; if no gain, revert to baseline config.
**Dependencies**: PM decision 15:45, VLM lock.

### [ ] WP2.2: Report evidence and ZIP check
**Owner**: python-developer (instance 2). **Deadline**: 16:20.
**May write**: `src/gameqa/report.py`, `tests/vision/test_report_evidence.py` (new), `docs/ali/evidence_shape.md`. Do not edit `storage.py`, `contracts.py`; use a sidecar `evidence.json` if a new field is needed (ask Celal for additive contract changes).
**Deliverable**: report contains input IDs/hashes, expected vs observed visual facts, applicable rule IDs, region/crop evidence, scope, final decision and reasons, model/prompt/config identity, unassessed areas; cache status honest (mixed/unknown; fresh namespace for measured runs). Evidence shape frozen and sent to Celal by 15:55.
**Acceptance**: test unzips an actual exported ZIP and asserts required input/crop/JSON/Markdown files; no invented repro steps or root causes; one real `analysis.json` + ZIP delivered to Celal by 16:10.
**Dependencies**: a real run (WP0.5/WP1.1 output).

### [ ] WP2.3: Commit, PR-ready bundle
**Owner**: git-workflow-master. **Deadline**: 16:35.
**Deliverable**: local commits on `feat/hackathon-vision-evidence`; push only if Ali explicitly asks; otherwise `git bundle`/patch under `artifacts/ali/` with base and head SHAs. No attribution trailers per project rule in CLAUDE.md; no force-push.
**Dependencies**: WP2.1, WP2.2 tests green.

### [ ] WP3.1: Frozen comparison run and visual review
**Owner**: experiment-tracker-pm (run, one runner, no concurrent VLM) + qa-engineer (visual checks). **Deadline**: 17:30 (A3).
**May write**: `docs/ali/A3_review.md`, `artifacts/ali/a3/**`, `configs/ali_a3.yaml`.
**Acceptance**: B and C share model/provider/rules/aligned inputs; no errors/duplicates/missing IDs; cached vs fresh recorded; REVIEW cases retained; at least one genuine failure or boundary example documented with image evidence; wording: "12 dev cases after tuning = development diagnostic"; the 60 eval set = historical regression only; no DINOv2 superiority claim unless counts show it.
**Dependencies**: freeze 16:50 config agreed with Celal.

### [ ] WP4.1: Demo and pitch evidence notes
**Owner**: documentation-engineer. **Deadline**: 18:30. **May write**: `docs/ali/DEMO_VIDEO_NOTES.md`, `docs/ali/PITCH_EVIDENCE.md`, `docs/ALI_HANDOFF.md` (Azerbaijani + English terms).
**Content**: 90-120 s shot list (problem; real FAIL with crop/rule; allowed PASS if achieved; honest REVIEW/failure; ZIP export; brief limitations); each cached/prerecorded segment marked; live wall time measured separately; pitch facts: what DINOv2 does, what the VLM does, what code decides, counts with denominators, missing cases, one failure, next pilot. Banned phrases: "fine-tuned", "production-ready", "reduces QA workload" without evidence.
**Dependencies**: WP3.1. Ali records the video.

### [ ] WP5.1: Acceptance check
**Owner**: qa-engineer. **Deadline**: 19:15. **May write**: `docs/ali/A5_acceptance.md`.
**Deliverable**: unzip a real evidence report, verify listed files; check pitch numbers against raw rows and denominators; package checklist (commit, launch command, model/config ids, input provenance, raw predictions, metrics, ZIP, video, pitch, limitations). Ali + Celal review; authorized human submits by 19:30.

## Quality Requirements
- [ ] Tests for behavior changes (pasted output); skips listed
- [ ] No background processes (no `&`); no servers unless required
- [ ] Experiments reproducible: seed, manifest hash, config hash, prompt version, commit SHA recorded
- [ ] Labels never reach inference; mocks labelled; secrets never printed
- [ ] Only Ali-owned files edited: judge.py, prompts.py, proposals.py, features.py(if needed), report.py, new helpers, configs/ali_*.yaml, tests/vision/*, docs/ALI_HANDOFF.md

## Technical Notes
**Risk**: RAM (4 GB free vs 9 GB needed) and Gemini quota; resolve at 14:55 probe. If 15:45 diagnostics are incomplete, use the predeclared balanced six, not a success-based pick.
