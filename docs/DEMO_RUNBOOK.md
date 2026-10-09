# Demo runbook

Provenance labels used below: **SYNTHETIC** = hand-drawn fixture in `data/fixtures/<case>/` (not benchmark data); **REAL BENCHMARK** = VideoGameQA-Bench pair (CC BY 4.0); **REAL MODELS** = DINOv2 on CUDA + Ollama `qwen2.5vl:3b`; **MOCK** = fault-injection judge, never real inference. "Observed" means a status file / senior-pm / my own run recorded it; otherwise UNVERIFIED or pending.

## Before the demo

1. Free RAM. The VLM runs on CPU and needs about 9.3 GiB free at load. Close the browser and heavy apps; if loading fails with "model requires more system memory", run `ollama stop qwen2.5vl:3b` and retry.
2. Ollama running with the model (`ollama list` shows `qwen2.5vl:3b`).
3. Launch: `.venv/bin/streamlit run app.py` (starts: VERIFIED by python-developer-app; open the URL it prints, normally http://localhost:8501).
4. Cold start: the first **Analyze** with real engines loads the VLM (55-70 s) and DINOv2 (about 6 s). Then an uncached pair takes about 85 s median (up to ~140 s). VLM replies are cached in `data/cache/vlm/`; a pair that was already analysed with the same config and prompt returns in 3-4 s. To show a fresh run, delete `data/cache/vlm/`.
5. Do not start a second real-VLM run while an evaluation is running on the same machine; they compete for RAM and CPU (D9).

## Using the app (all cases)

1. Sidebar: **VLM engine** = `Real (config)` (default) or `MOCK (fault injection)` with a behaviour dropdown. MOCK shows a red banner on the form and on the result.
2. **Pair source** = `Demo pair` and pick from the dropdown (entries are named `synthetic fixture | <case>` or `VideoGameQA-Bench | <sample_id>`), or `Upload two images`.
3. Check the **Rules** table (editable; `effect` is allow/deny). Fixture pairs bring their own `rules.yaml`; uploads start from `configs/rules_example.yaml`.
4. Press **Analyze**. The result shows the banner (green PASS / red FAIL / yellow NEEDS REVIEW) with the reason from `decide()`, `Engine: real (...)` or a MOCK / DEGRADED notice, both images with numbered boxes, one expander per region (crops, observed change, cited rules, evidence, validated flag), the whole-scene audit and Diagnostics (alignment, coverage, timings, versions, heatmap, overlap mask).
5. **Export bug report (ZIP)** downloads `<run_id>.zip` (also on disk as `artifacts/<run_id>.zip`, contains `report.md`, images, crops, `analysis.json`). The report says it carries no engine/build metadata or reproduction steps.
6. **Approve as new reference** (expander): type a Reference ID (defaults to the sample id), tick "I confirm this candidate becomes the new reference", press the button. Result line: "Previous version: v1 -> new version: v2". Files: `references/<id>/versions/v1.png` (the replaced reference), `v2.png` (the approved candidate), `history.json`. Nothing is replaced automatically; older versions are kept. Note: the button works for any decision, including NEEDS REVIEW and MOCK runs; the human confirms.
7. Sidebar **Saved runs** reopens any earlier run from `artifacts/`.

## Case 1: forbidden change -> FAIL (SYNTHETIC, REAL MODELS)

- Pair: `synthetic fixture | object_removed` (a barrel is deleted; `expected.json`: FAIL, true box `[444,209,506,271]`). Rules A1, A2 allow; D1, D2 deny.
- Observed (senior-pm, CLI, real engines): **FAIL**, real / complete, R1 forbidden citing D1. That run used the VLM cache (3-4 s). Artifact trace: `artifacts/20261008T230650Z-1335da` (walkthrough section 5). R1 box `[424,181,521,286]`, source union, scene audit `uncertain`.
- CLI equivalent: `.venv/bin/python -m gameqa.cli analyze --reference data/fixtures/object_removed/reference.png --candidate data/fixtures/object_removed/candidate.png --rules data/fixtures/object_removed/rules.yaml`
- Also observed (senior-pm): `allowed_and_forbidden` -> FAIL (R1 D1), real / complete.
- UI path (Analyze button with real engines): UNVERIFIED by me; the CLI uses the same `pipeline.analyze`.
- Say in the demo: the VLM called the object "a stack of brown blocks"; the verdict is right, the description is not reliable.

## Case 2: allowed change -> PASS (SYNTHETIC, REAL MODELS) - UNVERIFIED end to end

- Pair: `synthetic fixture | clothing_color_change` (shirt red -> blue; `expected.json`: PASS). Same rules; A2 should cover it.
- dl-engineer reports: neither proposal source fires (no region), the whole-scene audit answers `allowed A2`, validated. That makes it PASS-capable under `decide()` (no proposals, audit ran, allowed with evidence and an allow rule). **Not yet run through the full pipeline + `decide()` by anyone**; senior-pm will run it after E2. Until then treat the PASS as unverified and expect `NEEDS_REVIEW` as a fine outcome (an audit that is not validated cannot PASS).
- Do NOT use `lighting_change` for a PASS demo: it is expected PASS in `expected.json`, but the real run gave NEEDS_REVIEW (below).
- A PASS is reported as "a heuristic result, not proof that no bug exists".

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
| `vr_73635d70` | Youtube-Cutscene | 1278x718 | no_bug | pending |
| `vr_536596f0` | Youtube-Cutscene | 1232x718 | bug | pending |
| `vr_2ada9903` | Youtube-Cutscene | 1278x718 | no_bug | pending |
| `vr_b5647b43` | UnityCapturesDataset | 3840x2160 | bug | pending |
| `vr_9aa8a337` | Youtube-Cutscene | 1278x718 | bug | pending |

Expectations from measurements on the dev split (not promises): cutscene pairs differ globally, so the global-change collapse usually yields one full-frame region with `truncated=true` and therefore `NEEDS_REVIEW` at best; dev Unity bug pairs mostly ended uncertain/allowed with no validated `forbidden`. Do not present these as accuracy. CLI for all five: `.venv/bin/python -m gameqa.cli batch --split demo --out artifacts/demo_results.jsonl` (estimate 5-10 min uncached, not measured; run only when no evaluation is running).

## Reproduce a known failure

- Small object: fixture `small_object_removed` (12 px coin). DINOv2 alone misses it (max distance 0.35 = threshold); the classical source proposes it; the real VLM answered forbidden D1 in dl-engineer's smoke run. To see the DINOv2-only miss, run with `--config` containing `proposals: {sources: [dinov2]}` (UNVERIFIED by me).
- Allowed change with no proposal: `clothing_color_change` yields zero proposals; the decision then rests on the scene audit alone (Case 2).
- Bad VLM audit on a removal: in `artifacts/20261008T230650Z-1335da` the audit says `allowed A1/A2` for a missing barrel and is rejected by `validate_response`.

## Reset between demos

`artifacts/` and `references/` are git-ignored working data. Remove `references/<id>/` to forget an approval; delete `data/cache/vlm/` to force fresh VLM calls.
