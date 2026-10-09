# Celal C1 — frozen real demo gate

**READY — bir real bug üçün bounded demo gate.** Frozen bundle yoxlanıldı; human-labelled missing barrel üçün bir fresh Gemini analysis **FAIL** verdi. Həmin run-un UI replay və ZIP download-u verified-dir. Bir seçilmiş dev uğuru model accuracy və ümumi QA automation sübutu deyil.

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

Labels frozen dev annotations-dur; untouched holdout deyil. A1 təxminən **15:21**-də, **15:38** label freeze-dən əvvəl başladı. Ali diagnostic-də confirmation-dan əvvəl outputs-a baxmadığını bildirir; bu, attributed statement-dir. Bir neçə assistant correction əvvəlki balanced-six outputs-u görmüş assistant-dan gəlib. Bu provenance qorunur; labels fully blind kimi təqdim edilmir.

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
- Rules YAML SHA256: **9c27faab5f1e1fef11243685ec1bf606cd70f7bbb0b8bf893a5f4acd0adcd62b**. Original və stored PNG byte hashes re-encoding səbəbilə fərqlənir; **decoded RGB pixels identical** ayrıca PIL ImageChops ilə yoxlanıldı. Original hashes inventory ilə, stored hashes ZIP evidence ilə match-dir; ölçü 3840×2160. Exact pairs input-pixel-identity.json-dadır.
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

C-də doqquz truncated run var. 0 false-PASS **100% REVIEW** hesabınadır; decision coverage always-REVIEW ilə eynidir və QA işinin useful automatic azalmasını sübut etmir. Unity source yalnız bug-dur; class/source imbalance və label exposure comparisons-ı məhdudlaşdırır. Ali diagnostic-də observation correctness scored deyil. Bir fresh Gemini FAIL seçilmiş demo gate uğurudur, population improvement və fair full A/B/C ablation deyil.

## Ali confirmed checkpoint — C1 əlavəsi, inference təkrarlanmadı

User-confirmed pin **feat/hackathon-vision-evidence @ a5590a50849ace549debff63ad3f3b4e1a1f815a** artıq fetch edilmiş exact HEAD ilə eynidir. `git merge-base --is-ancestor` ilə aşağıdakı chain yoxlanıldı; full SHAs checkpoint-confirmation.json-dadır:

- cf861f1 — frozen dev12 selection.
- e844aab — frozen labels.
- cac62c7 — A1 tooling və configs/ali_a1_qwen.yaml.
- a502c2d — A1 diagnostic və predictions_A/B/C.jsonl.

**Qwen diagnostic identity:** `qwen2.5vl:3b`, prompt **v9**, config_hash **3a144cfcbb67**; raw A/B/C rows bu hash-i təsdiqləyir. Bu identity current Gemini barrel demo **gemini-3.5-flash / v9 / 6cfbba559386** identity-sindən ayrıdır. A1 table və onun coverage nəticələri Qwen diagnostic-ə aiddir, current Gemini result deyil.

Pinned `docs/ali/labels_audit.md` oxundu: audit **post-freeze və A1 outputs görüldükdən sonra** aparılıb. Frozen labels file byte SHA unchanged-dir.

- **vr_c1f47c57:** audit description correction — statue-nin altındakı **stone pedestal missing**-dir; small table object deyil. D1 qalır; audit uncertainty-ni low təklif edir. Frozen CSV-dəki description/medium dəyişdirilmədi. Bu case üçün yeni visual inspection/inference edilmədi; burada Ali audit finding-i attributed olunur.
- **vr_330651ed:** English → Portuguese subtitles və slight pose. Öz **cutscene D1 rules**-unda text changes ayrıca yoxdur; D1 support zəifdir. Ambiguous demo kimi təqdim edilir, frozen **D1/high** saxlanılır; yeni ambiguous ground-truth class yazılmır.

Sensitivity-only hesabı: vr_330651ed scoring üçün clean sayılsa **4 bug / 8 clean** olur. Raw predictions-dan müstəqil recompute edildi; labels faylı dəyişdirilmədi, inference yoxdur:

| Arm | Bug false-PASS | Clean PASS | Decision coverage |
|---|---|---|---|
| A pixel | **4/4** | 8/8 | 12/12 |
| B Qwen full-frame | **4/4** | 4/8 | 8/12 |
| C Qwen hybrid | **0/4** | 0/8 | **0/12 — all REVIEW** |

Bu sensitivity əsas nəticəni dəyişmir: A/B bugs-u PASS edir, C avtomatik qərar vermir.

Ali-nin pinned `docs/ali/a1_evidence/stage1_qwen_vs_gemini.json` reproducer-i oxundu, local evidence copy saxlanıldı. Artifact eyni composite PNG və stage-1 prompt ilə Qwen/Gemini comparison olduğunu bildirir:

| Pair | Qwen stage-1 reported | Gemini stage-1 reported |
|---|---|---|
| vr_4b921c5d | different texture and lighting effect on barrels | large barrel disappeared; stand empty |
| vr_d07179d5 | telephone booth replaced by a red mirror | booth roof and TELEPHONE sign disappeared |

Bunlar Ali-nin **prior same-crop perception reproducer** nəticələridir (n=2), yeni C1 calls deyil və accuracy measurement sayılmır. Current C1 barrel run ayrıca fresh end-to-end **FAIL**-dır. Crop-un təsvir etdiyi change-in görünə bilməsi üçün diagnostic evidence verir; digər cases üzrə generalization sübut etmir.

Bu əlavədə API attempts **4/8** olaraq qaldı; yeni run, UI inference, model/config change və ya cherry-pick yoxdur. Original **16:15 Asia/Baku cutoff** saxlanıldı.

## Remaining blockers / stop

Broader coverage and accuracy unverified; allowed/subtitle cases have no fresh Gemini result. Scene semantic uncertainty remains. Label assistant exposure makes these dev data unsuitable as a fresh improvement holdout. Native DINO identity still reports weights_sha256=unknown under custom TORCH_HOME (actual weights were preserved from the previous verified runtime). Hosted quota availability is not known. No vision/policy intervention, deployment, training or follow-on roadmap work.

Local evidence index: bundle-verification.json, candidate-labels.json, candidate-contact-sheet.jpg, barrel-inspection.jpg, gemini.yaml, barrel-rules.yaml, capture/, a1-artifact-provenance.json, a1-recomputed.json, zip-verification.json, ui-verification.json, ui-replay.jpg, runs/. Owned UI test service stopped at finalization; original services untouched.
