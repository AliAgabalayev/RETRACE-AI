# Demo runbook

Provenance labels used below: **SYNTHETIC** = hand-drawn fixture in `data/fixtures/<case>/` (not benchmark data); **REAL BENCHMARK** = VideoGameQA-Bench pair (CC BY 4.0); **REAL MODELS** = DINOv2 on CUDA + Ollama `qwen2.5vl:3b`; **MOCK** = fault-injection judge, never real inference. "Observed" means a status file / senior-pm / my own run recorded it; otherwise UNVERIFIED or pending.

## Before the demo

1. Free RAM. The VLM runs on CPU and needs about 9.3 GiB free at load. Close the browser and heavy apps; if loading fails with "model requires more system memory", run `ollama stop qwen2.5vl:3b` and retry.
2. Ollama running with the model (`ollama list` shows `qwen2.5vl:3b`).
3. Launch: `.venv/bin/streamlit run app.py` (starts: VERIFIED by python-developer-app; open the URL it prints, normally http://localhost:8501).
4. Cold start: the first **Analyze** with real engines loads the VLM (55-70 s) and DINOv2 (about 6 s). Then an uncached pair takes about 70 s median in the E2 evaluation (mean 116 s, p90 238 s; benchmark demo pairs 75-262 s). VLM replies are cached in `data/cache/vlm/`; a pair that was already analysed with the same config and prompt returns in 3-4 s. To show a fresh run, delete `data/cache/vlm/`.
5. Do not start a second real-VLM run while an evaluation is running on the same machine; they compete for RAM and CPU (D9).

## Using the app (all cases)

1. Sidebar: **VLM engine** = `Real (config)` (default) or `MOCK (fault injection)` with a behaviour dropdown. MOCK shows a red banner on the form and on the result.
2. **Pair source** = `Demo pair` and pick from the dropdown (entries are named `synthetic fixture | <case>` or `VideoGameQA-Bench | <sample_id>`), or `Upload two images`.
3. Check the **Rules** table (editable; `effect` is allow/deny). Fixture pairs bring their own `rules.yaml`; uploads start from `configs/rules_example.yaml`.
4. Press **Analyze**. The result shows the banner (green PASS / red FAIL / yellow NEEDS REVIEW) with the reason from `decide()`, `Engine: real (...)` or a MOCK / DEGRADED notice, both images with numbered boxes, one expander per region (crops, observed change, cited rules, evidence, validated flag), the whole-scene audit and Diagnostics (alignment, coverage, timings, versions, heatmap, overlap mask).
5. **Export bug report (ZIP)** downloads `<run_id>.zip` (also on disk as `artifacts/<run_id>.zip`, contains `report.md`, images, crops, `analysis.json`). The report says it carries no engine/build metadata or reproduction steps.
6. **Approve as new reference** (expander): type a Reference ID (defaults to the sample id), tick "I confirm this candidate becomes the new reference", press the button. Result line: "Previous version: v1 -> new version: v2". Files: `references/<id>/versions/v1.png` (the replaced reference), `v2.png` (the approved candidate), `history.json`. Nothing is replaced automatically; older versions are kept. Since D11 a run that is not a real-engine PASS (FAIL, NEEDS REVIEW, MOCK, DEGRADED) shows a warning and a second checkbox "I reviewed the regions and override the verdict"; the CLI refuses it without `approve --force` (exit code 3). A real-engine PASS needs only the first checkbox. Nothing here is automatic.
7. Sidebar **Saved runs** reopens any earlier run from `artifacts/`.
8. Sidebar **Reload models** clears the cached DINOv2/VLM engines (D11). Use it after a model load failure (for example not enough RAM): otherwise every later run stays `degraded` until Streamlit restarts.

### Headless UI check (no browser)

`.venv/bin/python scripts/ui_smoke.py [pair-substring]` (default `object_removed`) drives `app.py` with Streamlit `AppTest` and the real engines: choose a demo pair, Analyze, check the verdict is rendered, rerun (must not repeat inference), approve (v1 + v2 + history). Outputs go to a temp directory. senior-pm ran it: it passed, with the VLM answers coming from the disk cache of an earlier real run. It tests `app.py` logic, **not a real browser**; a click-through in Chrome was NOT verified (extension not connected).

## Case 1: forbidden change -> FAIL (SYNTHETIC, REAL MODELS)

- Pair: `synthetic fixture | object_removed` (a barrel is deleted; `expected.json`: FAIL, true box `[444,209,506,271]`). Rules A1, A2 allow; D1, D2 deny.
- Observed (senior-pm, CLI, real engines): **FAIL**, real / complete, R1 forbidden citing D1. That run used the VLM cache (3-4 s). Artifact trace: `artifacts/20261008T230650Z-1335da` (walkthrough section 5). R1 box `[424,181,521,286]`, source union, scene audit `uncertain`.
- CLI equivalent: `.venv/bin/python -m gameqa.cli analyze --reference data/fixtures/object_removed/reference.png --candidate data/fixtures/object_removed/candidate.png --rules data/fixtures/object_removed/rules.yaml`
- Also observed (senior-pm): `allowed_and_forbidden` -> FAIL (R1 D1), real / complete.
- UI path: the headless `scripts/ui_smoke.py` passed (Analyze rendered FAIL, rerun did not re-infer). A real browser click is UNVERIFIED.
- Also observed (senior-pm): `small_object_removed` -> FAIL (R1 `[324,294,349,319]`, classical source, forbidden D1; run `20261009T065813Z-43cffa`).
- Say in the demo: the VLM called the object "a stack of brown blocks"; the verdict is right, the description is not reliable.

## Case 2: allowed change -> PASS (SYNTHETIC, REAL MODELS)

- Pair: `synthetic fixture | clothing_color_change` (shirt red -> blue; `expected.json`: PASS). Same rules; A2 covers it.
- Observed (senior-pm, CLI, real engines; I read the artifact): **PASS**, real / complete, run `20261009T065807Z-0f8434`. 0 proposals (neither DINOv2 nor classical fires), whole-scene audit `allowed A2`, validated, evidence "The person in the red shirt has been replaced by a person in a blue shirt." Reason: "All 0 proposed region(s) judged allowed and the scene audit found no forbidden change. PASS is a heuristic result, not proof that no bug exists." `latency_s` is 0.0 in the audit, so the reply was most likely served from the VLM cache.
- Honest framing for a demo: this is one hand-drawn pair. On the real benchmark E2 produced a single PASS in 60 pairs and it was a false PASS (`vr_bcbcf341`, see "Reproduce a known failure"). Do not present the PASS as general ability.
- Also observed: `identical` -> PASS via the deterministic pixel-identical shortcut (run `20261009T065816Z-3054be`); no model decides there.
- Do NOT use `lighting_change` for a PASS demo: `expected.json` says PASS, the real run gave NEEDS_REVIEW (Case 3a).

## Case 3: uncertain / error -> NEEDS_REVIEW

- 3a. REAL MODELS, SYNTHETIC: `synthetic fixture | lighting_change` (global brightness/tint, objects present). Observed (senior-pm): **NEEDS_REVIEW**, R1 `uncertain`, real / complete. DINOv2 puts one tiny box on the sun; the 3B model cannot confirm anything; the system refuses to guess. This is the conservative behaviour, even though the fixture's `expected.json` says PASS.
- 3b. MOCK fault path (labelled MOCK everywhere): sidebar `MOCK (fault injection)` + `timeout`, pair `object_removed`, Analyze. CLI, verified by me on 2026-10-09 (real DINOv2 on CUDA, mock judge, scratch artifacts dir):

  ```
  .venv/bin/python -m gameqa.cli analyze --reference data/fixtures/object_removed/reference.png \
      --candidate data/fixtures/object_removed/candidate.png \
      --rules data/fixtures/object_removed/rules.yaml --mock timeout
  ```

  Output: `Decision: NEEDS_REVIEW  [MOCK: not real inference]`, `Mode: mock / degraded`, reason "R1: mock judgment (not real inference); SCENE: mock judgment (not real inference)". The raw `provider error ... TimeoutError: mock timeout` is inside each judgment's `errors` (visible in the region expander). `--mock allowed` and `--mock forbidden` also end in `NEEDS_REVIEW`: a mock can never PASS or FAIL. Other behaviours: `uncertain`, `invalid_json`, `unknown_rule`.
- 3c. Real error path without a mock: stop Ollama (`ollama stop` only unloads the model; to simulate "unavailable" stop the service) and Analyze: expect `DEGRADED` banner and `NEEDS_REVIEW`. UNVERIFIED by me.

## Five REAL BENCHMARK pairs (split `demo` of `data/manifests/inference_manifest.json`)

Shown in the app as `VideoGameQA-Bench | <sample_id>`. Rules come from the manifest (`A1` = the benchmark's ACCEPTABLE list, `D1` = its UNACCEPTABLE list, D8). The ground truth below comes from `data/manifests/eval_labels.json` (demo ids only; the inference path never reads it).

| sample_id | source | size | ground truth | pipeline outcome |
| --- | --- | --- | --- | --- |
| `vr_73635d70` | Youtube-Cutscene | 1278x718 | no_bug | NEEDS_REVIEW; 1 region (full-frame, truncated); 75 s |
| `vr_536596f0` | Youtube-Cutscene | 1232x718 | bug | NEEDS_REVIEW; 1 region (truncated), R1 invalid/failed response; 79 s |
| `vr_2ada9903` | Youtube-Cutscene | 1278x718 | no_bug | NEEDS_REVIEW; 12 proposals, 8 judged (truncated), several uncertain; 261 s |
| `vr_b5647b43` | UnityCapturesDataset | 3840x2160 | bug | NEEDS_REVIEW; 8 regions, 7 invalid/failed responses + 1 uncertain, scene audit failed; 260 s |
| `vr_9aa8a337` | Youtube-Cutscene | 1278x718 | bug | NEEDS_REVIEW; 1 region (truncated), R1 invalid/failed response; 79 s |

Observed (senior-pm, real engines, `.venv/bin/python -m gameqa.cli batch --split demo --out artifacts/demo/demo_split.jsonl`; all rows `real` / `complete`): **all 5 NEEDS_REVIEW**, 75-262 s each, so about 12 min for the batch. Regions per pair: 1, 1, 12 (8 judged), 8, 1. The pipeline neither confirmed nor missed a bug on these: it abstained. The 3B model often returned a response rejected by `validate_response` ("invalid or failed model response"). This matches the E2 picture (58 of 60 NEEDS_REVIEW). Do not present these as accuracy. Run the batch only when no evaluation or other real-VLM test is running.

## Reproduce a known failure

- **False PASS on the benchmark: `vr_bcbcf341`** (Unity, ground truth bug, split eval, in the 60-pair subset). E2 returned PASS: proposal R1 `[1213,1973,3003,2160]` correctly covers the road where the ground texture is missing in the candidate, but the VLM called it "license plate more visible" -> `allowed A1`, and the scene audit said "brighter lighting" -> `allowed A1`; both validated, so `decide()` passed (D11). The original run is saved: `artifacts/20261009T003250Z-58905e` (`analysis.json`, `crops/`, `rules.yaml`; 1 region, `real` / `complete`, 61.5 s). To inspect it, open `report.md` there. To re-run it (calls the real VLM, so do it only when nobody else is using Ollama; NOT repeated by me; the reply may differ if the cache is cleared and the model changes):

  ```
  .venv/bin/python -m gameqa.cli analyze --reference data/work/vr_bcbcf341/reference.png \
      --candidate data/work/vr_bcbcf341/candidate.png \
      --rules artifacts/20261009T003250Z-58905e/rules.yaml --sample-id vr_bcbcf341
  ```

  `rules.yaml` in that run directory is the A1/D1 pair taken from the manifest. Do not "fix" it by tuning on this eval id (it would use a label).
- Small object: fixture `small_object_removed` (12 px coin). DINOv2 alone misses it (max distance 0.35 = threshold); the classical source proposes it; the real run is FAIL with the classical box (run `20261009T065813Z-43cffa`). To see the DINOv2-only miss, run with `--config` containing `proposals: {sources: [dinov2]}` (UNVERIFIED by me).
- Allowed change with no proposal: `clothing_color_change` yields zero proposals; the decision rests on the scene audit alone (Case 2: PASS).
- Bad VLM audit on a removal: in `artifacts/20261008T230650Z-1335da` the audit says `allowed A1/A2` for a missing barrel and is rejected by `validate_response`. (That artifact predates the engine-mode fix and says `degraded`; `artifacts/20261008T230730Z-818bb9` is the same pair as `real` / `complete`.)

## Reset between demos

`artifacts/` and `references/` are git-ignored working data. Remove `references/<id>/` to forget an approval; delete `data/cache/vlm/` to force fresh VLM calls.
