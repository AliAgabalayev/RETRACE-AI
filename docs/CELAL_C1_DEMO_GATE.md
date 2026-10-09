# Celal C1 — frozen real demo gate

**READY — bounded single-bug demo gate.** Frozen bundle verified; one fresh Gemini analysis on the human-labelled missing barrel returned **FAIL**. Exact run UI replay and ZIP download verified. One selected dev success does not establish model accuracy or general QA automation.

## Scope / Git / vaxt

- Start **2026-10-09 15:55:00 Asia/Baku**; cutoff **16:15** (20 minutes). Only one fresh pair; no batch/model sweep, billing change, install, download or Ali-host job.
- Feature branch `feat/hackathon-demo-integration`; incoming checkpoint `0e234d858b036235d8b9b9b5c5dc62a292f48635` (initial working tree clean).
- Fetched Ali HEAD **a5590a50849ace549debff63ad3f3b4e1a1f815a**.
- Frozen original label commit **e844aab9239ad6b851ce426b7baba6706693e9f7**, author/commit time **15:38:44 Asia/Baku**; unchanged between that commit and fetched HEAD; file SHA256 **524583859358b6dcea8250325f88fbc12077cf5f0e3516fbe05f2e94a86bb96d**.
- Only label commit imported → local **d94af314d5ff038ed473051b89dae3e9a827065f**, also execution HEAD. Adapter/report imports already present from previous task; no duplicate cherry-pick.
- Inspected cac62c7 tooling/judge diff: opt-in input dump/cache records + runner/scorer; report had no newer delta. No need to import tooling because the existing bounded network observer records the four actual calls. Ali-owned vision/judge/prompts/report untouched. Final delivery SHA in chat and ignored `final-git-state.json`.

## ZIP verification və label provenance

Desktop `dev12_bundle_for_celal.zip`: **64,103,616 bytes**, SHA256 **70089e2499136fdba8a4e1f33c6f3296d5334742c3302f8361af32a8f866ce23**, `testzip() is None`. **24/24 image hashes and dimensions match inventory.json**, 12 pairs. Explicit path mapping: remove the exact `artifacts/ali/` prefix from inventory `artifacts/ali/bundle/<id>/<side>.png` to ZIP member `bundle/<id>/<side>.png`; extract only verified images into new ignored `artifacts/c1-demo-20261009/bundle/`.

Supplied `20261009T105011Z-fbde6e.zip`: integrity valid, SHA256 **cc592761a0ca4e69eb725166a3419cd53bd6cd537a26709d2d2e1c063d3f53a1**. Actual sample **vr_59af7164**, allowed clothing/A1 observation, final **NEEDS_REVIEW**, cache **unknown (replay possible)**. This is a supplied historical clothing report, not a fresh barrel result.

Labels are frozen dev annotations, not independent untouched truth. A1 started around **15:21**, before the **15:38** label freeze. Ali's diagnostic says he did not inspect outputs before confirmation; this is an attributed statement. Several assistant-proposed corrections came from an assistant already exposed to earlier balanced-six outputs. Preserve that provenance and do not describe the labels as fully blind.

| Candidate | Actual frozen label / uncertainty | Rationale / provenance | Local image inspection / current execution |
|---|---|---|---|
| vr_4b921c5d — missing barrel | **D1 / medium**, out_of_scope=N; bbox [2540,1500,3000,2050] | `claude_correction; confirmed by Ali`; Ali originally wrote no significant change, localized diff prompted correction | Before barrel present, after stand empty; close crop inspected. **Fresh Gemini FAIL**, below |
| vr_09a066d3 — outfit | **A1 / low**, out_of_scope=N; bbox [0,55,925,718] | Clothing customization; `ali; bbox corrected by claude` | Blue casual shirt → grey suit jacket visible. No fresh VLM/diagnostic run |
| vr_330651ed — subtitle | **D1 / high**, out_of_scope=N; bbox [0,0,1279,718] | `claude_draft; confirmed by Ali`; textual/UI change vs expected dynamic text is disputed | English → Portuguese subtitles visible. Ambiguous presentation, **frozen ground truth remains D1**. No fresh VLM/diagnostic run |

Contact sheet and barrel inspection crop are local visual evidence. The three are selected development demonstrations, not an independent evaluation set. No additional local proposal diagnostics were needed beyond the barrel's actual pipeline run.

## Fresh barrel result — EXECUTED / MEASURED

- Run **20261009T115633Z-83936b**, sample **vr_4b921c5d**, model **gemini-3.5-flash**; engine real, CUDA float32 frozen DINOv2, prompt **v9**, config hash **6cfbba559386**.
- Reused exact provider settings from configs/gemini_integration.yaml: OpenAI-compatible Google endpoint, image_detail=null, reasoning_effort=low, temperature=0, timeout=60s, max_attempts=1, transient_retries=0. Only run directories changed to new `artifacts/c1-demo-20261009/{cache,runs,references}`. Original env/cache/model/history preserved.
- Human labels and expected verdicts never passed to the CLI or prompts. CLI inputs were the two original verified images and **exact inventory A1/D1 rules**; equality with AnalysisResult rules asserted. Unity rules differ from cutscene rules; no substitute generic rules were used.
- Original inventory reference SHA256: **1b9f503b677e6c547aad6b835d6ca95b2407cd8bd3123911d9d30ae30040ef18**.
- Original inventory candidate SHA256: **a8c2321f4237f8c36483d87762f020806901dfe30ba733585fb3dd00be750a98**.
- Rules YAML SHA256: **9c27faab5f1e1fef11243685ec1bf606cd70f7bbb0b8bf893a5f4acd0adcd62b**. Original/stored input hash equality is separately checked via ZIP evidence; stored pixel size 3840×2160.
- Alignment **identity**, overlap **1.0**; R1 **[2484,1400,3049,1966]**, source **union**, one proposal judged, truncated=false, no deadline expiry. Localized proposal covers the missing barrel.
- Region observation: **The large wooden barrel has disappeared from the wooden stand.**
- Region judgment: **forbidden / D1**, validated=true, errors=[]. Exact evidence: **The AFTER screenshot shows that 'the large wooden barrel is missing, leaving only small wooden blocks on the stand', which constitutes a missing key scene element.**
- Scene observation: **The wooden barrel inside the yellow box R1 has disappeared in the AFTER image.** Scene stage-2: **uncertain**, rule_ids=[], validated=true, errors=[]; unsure whether barrel is a key scene element or non-critical background. extra_changes_reported=false. This disagreement remains visible.
- Actual final policy: **FAIL**. Exact reason: **Forbidden change with visual evidence: R1 (D1).** No decisive blocker for this selected run; valid localized forbidden region triggers the existing FAIL policy despite the uncertain scene judgment. No forced verdict or guard/prompt/threshold/crop adjustment.

| Actual network call | Stage | Cache | HTTP | Latency |
|---|---|---|---|---|
| 1 | R1 image observation | live, cache_hit=false | 200 | 2.4393s |
| 2 | R1 text rule judgment | live, cache_hit=false | 200 | 1.5505s |
| 3 | Scene image observation | live, cache_hit=false | 200 | 3.1210s |
| 4 | Scene text rule judgment | live, cache_hit=false | 200 | 3.0646s |

**4/8 attempts** consumed; retries=0, warmup generation=0, no quota error. CLI wall **25.4442s**, pipeline **18.4305s**, DINO features **0.5709s**. Calls captured from actual network, new cache initially absent; no replay response used in fresh CLI inference. Remaining account quota not measured; remaining task budget 4 calls not used.

Ali evidence.json keeps `unknown (replay possible)` and per_stage_recorded=false because its schema/result does not store call hits. Freshness is proven separately by included provider-capture records and runtime identity. Do not overwrite the schema's unknown status with an unsupported per-stage assertion.

## Export / UI / checks

- ZIP `artifacts/c1-demo-20261009/runs/20261009T115633Z-83936b.zip`: **25 entries**, `testzip() is None`; evidence.json schema_version=1 and documented fields checked. Includes analysis.json, report.md, rules.yaml, input/aligned/overlay images, crops, diagnostics, provider requests/responses/images, runtime config/input identity.
- Input, aligned candidate, rules and both crop SHA256 fields independently recomputed from ZIP member bytes; all match. Key-value and Authorization-header scan clean. Observer persists no headers or environment credentials.
- Actual browser **saved-run REPLAY** on localhost:8524: correct run ID/sample, FAIL reason, R1 box/crops, validated forbidden observation and uncertain scene visible. **No fresh UI Analyze**, avoiding duplicate inference.
- Actual Export ZIP browser download completed at `C:/Users/celal/Downloads/20261009T115633Z-83936b.zip`; downloaded ZIP opens and every member byte matches server archive. Download SHA256 **3dfaa801a1b5c92dc4b2ae1432f4e0151d0acfb4ea0d15f97810619d6196ae28**. One saved run, four provider records after UI replay/export.
- Existing targeted non-model tests: `pytest tests/vision/test_report_evidence.py tests/vision/test_openai_provider.py -q -ra -p no:cacheprovider --basetemp <new temp directory>` → **18 passed, 0 skipped, 1.42s**, exit 0. This checks adapter contracts/export, not model accuracy. No integration source changes in C1; previous integration suite 186-pass result remains prior evidence, not rerun here.
- `git diff --check` clean. Labels + this document are the only new tracked changes. All assets/config/cache/captures/ZIPs under new ignored C1 artifact root; prior evidence unchanged.

## Ali A1 — dev diagnostic validity

Committed raw predictions_A/B/C.jsonl were read from fetched exact HEAD and independently recounted against frozen labels; **no inference rerun**:

| Arm | PASS / FAIL / REVIEW | Decision coverage | Bug false-PASS (5 bugs) | Clean PASS (7 clean) |
|---|---|---|---|---|
| A pixel | 12 / 0 / 0 | 12/12 | 5/5 | 7/7 |
| B Qwen full-frame | 8 / 0 / 4 | 8/12 | 5/5 | 3/7 |
| C Qwen hybrid | 0 / 0 / 12 | **0/12** | 0/5 | 0/7 |

C has nine truncated runs. Its 0 false-PASS is explained by **100% REVIEW**, equivalent to always-REVIEW decision coverage; it proves no useful automatic reduction of QA work. Unity source is bug-only; class/source imbalance and label exposure limit comparisons. Observation correctness was not scored in Ali's diagnostic. The fresh one-case Gemini FAIL is a successful selected demo gate, not a measured population improvement or a fair full A/B/C ablation.

## Remaining blockers / stop

Broader coverage and accuracy unverified; allowed/subtitle cases have no fresh Gemini result. Scene semantic uncertainty remains. Label assistant exposure makes these dev data unsuitable as a fresh improvement holdout. Native DINO identity still reports weights_sha256=unknown under custom TORCH_HOME (actual weights were preserved from the previous verified runtime). Hosted quota availability is not known. No vision/policy intervention, deployment, training or follow-on roadmap work.

Local evidence index: bundle-verification.json, candidate-labels.json, candidate-contact-sheet.jpg, barrel-inspection.jpg, gemini.yaml, barrel-rules.yaml, capture/, a1-artifact-provenance.json, a1-recomputed.json, zip-verification.json, ui-verification.json, ui-replay.jpg, runs/. Owned UI test service stopped at finalization; original services untouched.
