# qa-engineer status

## Defects (policy, frozen decision.py -- owner: senior-pm / python-developer)

### QA-D1 (important) allowed verdict citing a deny rule still PASSes
Repro: `decide(DecisionInput(rules=[A1 allow, D1 deny], judgments=[RegionJudgment(region_id="R1", verdict=allowed, rule_ids=["D1"], evidence="x", validated=True, model="ollama:q")], scene_audit=<clean allowed audit>, coverage=Coverage(proposals_total=1, proposals_judged=1, scene_audit_ran=True), alignment=<identity>))` -> PASS.
Expected: NEEDS_REVIEW (self-contradictory response). Either decision.py or the judge validator (validated must be False) must catch it. Test: tests/policy/test_decision.py::test_allowed_verdict_citing_deny_rule_is_not_pass (xfail strict).

### QA-D2 (minor) allowed verdict with no rule_ids and empty evidence PASSes
Same setup, `rule_ids=[]`, `evidence=""`. Unverifiable "allowed" -> PASS. Suggest require evidence for allowed or validator rejection. Test xfail strict.

### QA-D3 (important) conflicting rules are not detected anywhere in decision layer
`rules=[A1 allow "Trees may disappear", D1 deny "Trees may disappear"]` with a clean run -> PASS. Brief section 6: conflicting rules -> review. Needs a conflict check (pipeline/rules.py can flag and pass pipeline_errors or a new DecisionInput field). Test xfail strict.

Verified OK: forbidden precedence, mock/unvalidated/errored forbidden never FAIL, truncation/audit/empty rules/alignment/deadline never PASS, identical shortcut.
Note: identical_images shortcut returns PASS even with empty rules and pipeline_errors (documented shortcut; acceptable).

## Progress
- [x] tests/conftest.py, tests/policy/test_decision.py (46 pass, 3 xfail = defects above)

### QA-D4 (important, owner dl-engineer) translation leaves a full-frame classical proposal
Repro: `.venv/bin/python -m pytest tests/acceptance/test_coordinates.py -k flood` (fixture small_translation: shift +4,+3). align() -> ALIGNED (shift -4,-3, correct). propose(classical only) -> single box (0,0,640,360). Cause: GaussianBlur(sigma 2) of the warped candidate bleeds the black invalid border ~4-6 px into the valid mask region, `diff>40 & valid` forms an L-shaped edge band, close+bbox -> whole frame. Interior max diff is 0. Fix: erode overlap mask by >=3*sigma (or masked/normalized blur / BORDER_REPLICATE warp) before thresholding. Impact: any aligned (shifted) pair yields a whole-frame region for the VLM; wrong crops, wasted judgment, likely false review. Required verification: test flips (xfail strict will error "XPASS" -> remove marker).

### QA-D5 (important, owner dl-engineer) 12 px coin removal produces zero proposals (classical)
Repro: tests/acceptance/test_coordinates.py[small_object_removed]; propose() returns []. Disk area ~113 px < min_area (0.0005*HxW = 115) and blurred yellow-vs-green diff. Zero proposals + clean audit => PASS is allowed by decision.py, so this is a real miss path; the scene audit is the only safety net. DINOv2 path not yet measured here.
