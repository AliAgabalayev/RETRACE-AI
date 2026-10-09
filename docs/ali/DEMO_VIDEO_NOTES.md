# Demo video notes — target 113 s, hard limit 90–120 s

**C5 status update:** current fetched integration487f202, actual combined offline suite199passed6skipped. Compact `deploy/replay/barrel/` saved-run package/captures artıq localdır; bütün12C2ZIP/pedestal bundle kimi təqdim edilmir. Aşağıdakı C2/C4 source identities historicaldır; runtime/policy unchanged-dir. Ali currentUI hələ79: final recording üçün latest integration fresh launch və run-bound export pre-flight qalır. [Current Git plan](GIT_FINALIZATION.md), [C5 provenance](../FINAL_GITHUB_STATE.md).

Status: **shot list hazırlanıb; UI video çəkildiyi və ya final video file yaradıldığı iddia edilmir**. Recording owner **Ali**, final slide assembly owner **Celal**. Motion evidence draft ayrıca artifact-dir; onun mövcudluğu UI recording və final acceptance tamamlandığını göstərmir. Video/slides deadline 18:45, daxili submission **19:30**, rəsmi deadline 20:00 Asia/Baku. **17:30-dan sonra feature, model experiment və threshold tuning yoxdur.**

Final runtime **C2 OpenRouter / google/gemini-3.5-flash**, reasoning low, prompt v9. C2 evidence source SHA **79a0ef740196cbaa0639579386c6c591d2bfd8ca**, canonical C config hash **eaa371255716**. C2 raw rows həmin checkout-dan QA tərəfindən **independently recompute edilib**. Latest C4 UI-ready delivery **68501897746bf674d582fd810cd9d7e2cfb943e6**, runnable UI code **be1ea0acce271df994b516f6fa297118e981a3dd**: [runbook](../FINAL_DEMO_RUNBOOK.md), [verification](../C4_DEMO_VERIFICATION.json). Celal host-da replay/browser export verified-dir; C4 fresh inference yoxdur. Actual ignored C2 ZIP bytes və Ali host-da C4 launch/browser export hələ verified deyil. **Local recording pre-flight qalır**; Qwen vision branch-dəki UI istifadə edilmir. [Pitch evidence](PITCH_EVIDENCE.md).

## Recording pre-flight — tamamlanma iddiası deyil

- [x] Celalın **C4 UI-ready SHA** repo confirmation-u alınıb: UI code be1ea0a, delivery6850189; freeze/source79 ayrı saxlanılır.
- [ ] Ali app həmin C4 checkout-dan fresh açılır. Cari :8501 self-test17:46-da79a0ef7 ilə restart edilib, köhnə11:30 instance deyil; final recording-dən əvvəl C4 source + artifact bundle pre-flight tələb olunur.
- [ ] Canonical runtime açıq seçilib: **GAMEQA_CONFIG=configs/openrouter_gemini_pilot.yaml**. Sidebar/version identity config hash eaa371255716 ilə uyğun gəlir. Credentials ekranda görünmür.
- [ ] C2 barrel saved run **20261009T123704Z-8e4e19**, pedestal **20261009T124621Z-0b0c2b**, outfit **20261009T123947Z-584a66** həmin UI host-da mövcuddur və açılır. Raw rows-un mövcudluğu ignored artifact binaries-in Ali host-da mövcudluğunu sübut etmir.
- [ ] UI-exported ZIP-də report.md, analysis.json, **evidence.json**, rules.yaml, images və crops açılır; decision/hash identity yoxlanır. C2 source ZIPs ignored-dir; Ali host-da local ZIP/download verification pending-dir.
- [ ] C4 UI-də **run-un stored rules** read-only görünür; Ali local pre-flight-də exact run rules təsdiqlənir. Köhnə UI qayda editoru ilə recorded rules qarışdırılmır.
- [ ] C4 **Saved run replay — no new inference** label-i kadrda saxlanılır; bütün cached/prerecorded segment-lər ayrıca caption daşıyır.
- [ ] .env, API key və terminal environment recording-də görünmür; mock engine seçilmir.
- [ ] Final video file metadata ilə **90–120 s** təsdiqlənir; cut markers, caveat-lər və submission package yoxlanır.

App launch (repo root-dan; bu sənəd özü launch etmiş sayılmır):

    GAMEQA_CONFIG=configs/openrouter_gemini_pilot.yaml .venv/bin/streamlit run app.py

Bu command yalnız config-i ehtiva edən **UI-ready integration checkout**-da istifadə olunur. Saved-run replay üçün Analyze basmaq lazım deyil; recording üçün yeni model job və batch rerun yoxdur.

## 113 saniyəlik shot list

Caption-lar segment ərzində oxunaqlı qalır. C2 metrics **raw records-dan verified** kimi göstərilə bilər; actual UI replay/export verification isə ayrıca UI-ready gate-dir.

| Time | Ekran / artifact | Azerbaijani voice-over | Segment label |
|---|---|---|---|
| 0:00–0:10 | Reference/candidate və title | “Yeni game build-də QA screenshot-ları müqayisə edir. İşıq dəyişə bilər; scene object-in yoxa çıxması isə bug ola bilər. Qaydaları vizual sübutla yoxlayan prototype qurduq.” | **PRERECORDED — real benchmark inputs** |
| 0:10–0:24 | Flow: screenshots + rules → proposals → observation → rule verdict → code decision | “Frozen DINOv2 və pixel diff region-ları seçir. VLM əvvəl rules olmadan görünüşü təsvir edir, sonra rules ilə hökm verir. Final PASS, FAIL və REVIEW-u deterministic code seçir.” | **PRERECORDED — pipeline slide** |
| 0:24–0:48 | Barrel before/after, R1 crop, stored D1, C2 FAIL; Qwen REVIEW yanında | “Burada barrel itib. C2 Gemini R1-də və scene audit-də D1 violation tapıb: FAIL. Eyni pair-də local Qwen bunu lighting kimi təsvir edib, REVIEW verib. Ekranda saxlanmış real nəticələri replay edirik.” | **REPLAY — C2 20261009T123704Z-8e4e19**; Qwen **REPLAY — A1 20261009T112802Z-c4530d** |
| 0:48–1:04 | [Pedestal zoom](a3_evidence/vr_c1f47c57_pedestal_zoom_ref_vs_cand.png), C2 PASS | “Əsas failure budur: statue-nin altındakı stone pedestal itib. Həm full-frame, həm hybrid yanlış PASS verib. Bu, allowed-change success deyil; bug-a verilmiş false-PASS-dir.” | **REPLAY — C2 20261009T124621Z-0b0c2b**; visual **PRERECORDED — real pedestal evidence** |
| 1:04–1:16 | Outfit vr_09a066d3, C2 saved REVIEW | “Allowed outfit change-i model görür, amma global-change collapse REVIEW yaradır. Genuine clean PASS əldə olunmayıb. C2-də yeganə PASS də bug-dur.” | **REPLAY — C2 20261009T123947Z-584a66** |
| 1:16–1:31 | Verified UI export/download, unzip: report, evidence.json, rules, crops | “Report ZIP input hashes, rules, crop-lar, scope, model identity və final reason saxlayır. VLM-in mətni unverified kimi göstərilir. Bu saved-run export-dur; yeni inference vaxtı deyil.” | **REPLAY — report from actual run_id; no new inference**; əvvəl çəkilibsə əlavə **PRERECORDED** |
| 1:31–1:48 | Qwen baseline + C2 tables, false-PASS yanında coverage | “12 development pair-də Qwen hybrid 0/5 false-PASS ilə 0/12 coverage verir. Gemini 3/5 bug-a FAIL verir: false-PASS 1/5, coverage 5/12. B və C aggregate counts-u eynidir; hybrid advantage göstərilməyib.” | **PRERECORDED — dev12 comparison, raw counts verified** |
| 1:48–1:53 | Closing + limitations | “Perception əsas bottleneck-dir. Fresh held-out pilot və ayrıca ablation növbəti addımlardır.” | **PRERECORDED — limitations** |

113 s plan real edit-in müddəti deyil: export olunan file duration ayrıca yoxlanır. 120 s aşılırsa outfit shot və title qısaldılır; **pedestal failure, false-PASS + coverage, replay labels və label provenance çıxarılmır**.

UI-ready və artifact transfer recording-ə çatmasa, UI shots əvəzinə **PRERECORDED — motion evidence draft, screenshots + saved raw results; UI recording pending** təqdim edilə bilər. Bu variant fresh UI Analyze/download claim-i vermir; submission capability öz actual statusu ilə göstərilir.

## Comparison slide üçün exact rəqəmlər

Qwen A1/A3: Ollama qwen2.5vl:3b, prompt v9. A1 config hash **3a144cfcbb67**, A3 **642b6e26f39d**. [Raw score](a1_evidence/score_raw.md), [A3 review](A3_review.md).

| Qwen baseline | PASS / FAIL / REVIEW | Bug false-PASS | Coverage | Clean PASS |
|---|---|---|---|---|
| A pixel | 12 / 0 / 0 | 5/5 | 12/12 | 7/7 |
| B full-frame VLM | 8 / 0 / 4 | 5/5 | 8/12 | 3/7 |
| C hybrid | 0 / 0 / 12 | 0/5 | 0/12 | 0/7 |

| C2 final runtime — raw counts independently verified | PASS / FAIL / REVIEW | Bug false-PASS | Coverage | Clean PASS / false-FAIL |
|---|---|---|---|---|---|
| B Gemini via OpenRouter | 1 / 4 / 7 | 1/5 | 5/12 (41.7%) | 0/7 / 2/7 |
| C Gemini via OpenRouter | 1 / 4 / 7 | 1/5 | 5/12 (41.7%) | 0/7 / 1/7 |

**Counts eynidir, pair-level results fərqlidir:** booth vr_d07179d5 C FAIL / B REVIEW; frozen-clean vr_ef9b073a C REVIEW / B FAIL. Buna görə “B və C bütün nəticələrdə eynidir” deyilmir. Frozen-clean vr_43773eb8 hər ikisində FAIL alır; visible subtitle absence ilə frozen A1 label arasında scope conflict var, frozen scoring-də false-FAIL saxlanılır.

Slide footer: **“dev12, n=12, 5 bug/7 clean; not held-out. Labels finalized after A1 began; 4/5 bug labels assistant-proposed, Ali-confirmed.”** C2 aggregate counts eynidir, amma **10/12 pair-level equality** var. C **3/5 bug FAIL**, B **2/5 bug FAIL**; həmin sayları “4 real bugs caught” kimi dəyişmək olmaz.

C2 **80 fresh calls, 0 cache hits, 0 retries, HTTP 200 80/80** və **provider-reported cost $0.2871945** raw records-dan independently recompute edilib; invoice independently verified deyil. C cost **$0.1934625 / 56 calls**, B **$0.0937320 / 24 calls**. Exact final delivery checkout-da QA actual suite **194 passed, 6 skipped, 5.14 s** alıb. Historical C2 **186 passed, 6 deselected, 0 skipped** Celalın execution report-udur; current test count deyil. Tests model accuracy ölçmür. C ZIP checks Celal host-da edilib; local actual archive checks və full request/image capture audit ayrıca pending-dir. [Raw C](../c2_openrouter/C_predictions.jsonl), [raw B](../c2_openrouter/B_predictions.jsonl), [calls](../c2_openrouter/calls.jsonl), [independent QA recompute](C2_RECOMPUTED.json).

A3 **36/36 rows** A1 ilə eynidir; A3 **80 fresh calls**, 0 cache hits. “Determinism check, same 12 pairs” yazılır; “second sample” deyil. Observation line əlavə edilərsə: **B y+p 4/12, C 9/12; strict y 1/12 each; one rater, partial credit, possible anchoring**. Bu crop perception signal-ıdır, DINOv2 advantage claim-i deyil.

## Artifact identity və fallback

| Shot | Exact identity | Verification sərhədi |
|---|---|---|
| C2 barrel FAIL | 20261009T123704Z-8e4e19; R1 [2484,1400,3049,1966]; region və SCENE forbidden/D1 | Committed raw C row oxunub; UI replay/export **UI-ready gate pending** |
| C2 pedestal false-PASS | 20261009T124621Z-0b0c2b; [pedestal zoom](a3_evidence/vr_c1f47c57_pedestal_zoom_ref_vs_cand.png) | Actual bug; C2 PASS real failure, allowed success deyil |
| C2 outfit REVIEW | 20261009T123947Z-584a66 | Model blue→gray outfit change-i təsvir edir; coverage/global collapse səbəbi açıq göstərilir |
| C1 barrel FAIL fallback | 20261009T115633Z-83936b; direct Google gemini-3.5-flash, v9, config hash 6cfbba559386 | **Celal host-da** fresh CLI + browser replay/download verified; Ali host-da archive pending; OpenRouter C2 kimi göstərilmir |
| Qwen barrel REVIEW | 20261009T112802Z-c4530d; [barrel crop](a1_evidence/vr_4b921c5d_R1_vlm_input.png) | [Ali browser replay](UI_BROWSER_CHECK.md), [raw C rows](a1_evidence/predictions_C.jsonl) |
| Qwen fallback ZIP | artifacts/ali/demo_zips/bug_vr_4b921c5d_C_20261009T112802Z-c4530d.zip | [QA](A5_acceptance.md) members/hashes yoxlayıb; **REVIEW ZIP**, Gemini FAIL kimi göstərilməməlidir |

C2 runtime identity: exact model **google/gemini-3.5-flash**, OpenRouter; prompt v9; C hash **eaa371255716**, B diagnostic hash **2dfeb64cd673** (paths/namespace fərqi). Historical C2 execution code SHA **c917532ac3161a0886f626985c53307eb2d477d8**; C3 implementation freeze SHA **bdd93fb534e8c0e9b574e60d383bc8b14dd03bf3**; final delivery **79a0ef740196cbaa0639579386c6c591d2bfd8ca**. Bunlar future UI-ready SHA ilə əvəzlənmir.

UI: sidebar → **Open a saved run** → actual run_id → **Load saved run**. Overlay **REPLAY — saved run <run_id>**. Download fresh inference deyil. ZIP göstərilməzdən əvvəl actual archive members yoxlanır. Raw rows-da mövcud olan B-vr_<sample> IDs native UI AnalysisResult saved runs və ZIPs deyil; **B üçün native report ZIP claim-i yoxdur**.

## Live timing — video müddətindən ayrı

Recording üçün yeni batch və model experiment yoxdur. Əldə olan measurements istifadə olunur:

| Runtime | Measured wall | Pipeline | Scope / source |
|---|---|---|---|
| C2 OpenRouter barrel | 31.520 s orchestration | 30.2167 s | Celal host, fresh C2 raw row, n=1; UI latency deyil |
| C2 C / B median | 39.99005 s / 19.7196 s | Wall field-dən | Eyni 12 dev pairs, Celal host; saved raw wall fields, UI latency deyil |
| Qwen barrel | 100.1 s CLI | 83.7 s | Ali host, fresh empty-cache CLI, resident CPU model; [UI_BROWSER_CHECK](UI_BROWSER_CHECK.md) |
| C1 direct Gemini barrel | 25.4442 s CLI | 18.4305 s | **Celal host**, n=1, 4 live calls; [C1 gate](../CELAL_C1_DEMO_GATE.md) |

Caption: **“Saved results replayed; wall time measured separately. C2 barrel 31.5 s on Celal host; Qwen barrel 100.1 s on Ali host; n=1 each, different hosts.”** Bu latency superiority measurement deyil. Video gözləmə hissəsini kəsirsə **TIME CUT** caption-u göstərilir; replay loading fresh inference timing kimi yazılmır. **LIVE** yalnız həqiqətən yeni inference gedən shot üçün istifadə edilir. Ayrı explicit job tələb olunarsa əvvəl artifacts/ali/vlm.lock götürülür; bir VLM job-dan artıq işləməz.

## Wording guardrails

- C2 barrel region **və scene forbidden**-dur. C1 fallback-da **scene uncertain** qalır, reliable R1/D1 FAIL yenə keçərlidir; bu iki run qarışdırılmır.
- **Qwen barrel FAIL** demək olmaz; Qwen nəticəsi REVIEW-dur.
- Pedestal PASS **false-PASS failure**-dır; C2-nin yeganə PASS-i genuine allowed change kimi göstərilmir.
- B=C yalnız aggregate counts-a aiddir. “Hybrid beats full-frame”, “DINOv2 improves accuracy”, “fine-tuned”, “production-ready”, “reduces QA workload” və generalization claim-ləri yoxdur.
- vr_330651ed subtitle case-i göstərilərsə **ambiguous** deyilir: cutscene rules-da text change rule-u yoxdur. Frozen labels dəyişdirilmir.
- **4/5 bug label assistant-proposed, Ali-confirmed**-dir; localization box agreement tam independent deyil. Pedestal proposals **classical**-dır, DINOv2 detection deyil.
- Hər replay/cached/prerecorded segment label daşıyır; mock real inference kimi göstərilmir. Native report cache status **unknown (replay possible)** qalır; freshness sübutu ayrıca provider records/calls.jsonl-dandır.
