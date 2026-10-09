# Pitch evidence — Ali, 9 oktyabr 2026

Final demo runtime **C2: Gemini 3.5 Flash via OpenRouter**-dır; **Qwen A1/A3 baseline** kimi qalır. QA exact final integration SHA **79a0ef740196cbaa0639579386c6c591d2bfd8ca** checkout-undan C2 raw rows, frozen labels, per-call records və identities-i **local olaraq independently recompute** edib. Runtime **google/gemini-3.5-flash**, reasoning low, prompt v9; canonical C config hash **eaa371255716**. **Actual C2 ZIP binaries və browser replay/export Ali host-da hələ yoxlanmayıb**. Recording Celalın ayrıca **UI-ready SHA** confirmation-unu gözləyir.

Scope: **development diagnostic on 12 pairs**, Ali-nin frozen labels-ı ilə **5 bug / 7 clean**. dev12 mixed-source-dur və **held-out deyil**. Labels A1 başlayandan sonra **15:38:44**-də finalized olub; **5 bug label-dan 4-ü assistant-proposed correction, Ali-confirmed**-dir. Bu caveat metric slide-da görünməlidir. [Label audit](labels_audit.md), [A3 review](A3_review.md).

## 1. Final runtime: C2 — raw rows independently verified

Coverage = (PASS + FAIL) / 12. False-PASS həmişə coverage ilə yanaşı göstərilir; REVIEW denominator-dan çıxarılmır.

| Arm | PASS / FAIL / REVIEW | Bug false-PASS | Coverage | Bug FAIL | Clean PASS | Clean false-FAIL |
|---|---|---|---|---|---|---|
| B full-frame, Gemini via OpenRouter | 1 / 4 / 7 | 1/5 | 5/12 (41.7%) | 2/5 | 0/7 | 2/7 |
| C hybrid, Gemini via OpenRouter | 1 / 4 / 7 | 1/5 | 5/12 (41.7%) | 3/5 | 0/7 | 1/7 |

Mənbə: [B raw predictions](../c2_openrouter/B_predictions.jsonl), [C raw predictions](../c2_openrouter/C_predictions.jsonl), frozen [labels](labels_ali.csv), [local independent recompute](C2_RECOMPUTED.json). Hər arm 12 unique IDs-dir; missing/duplicate/extra yoxdur. C2 hybrid **3/5 bug-a FAIL** verib; barrel **vr_4b921c5d** və booth **vr_d07179d5** bu uğurlara daxildir. Missing stone pedestal **vr_c1f47c57** isə **B və C-də yanlış PASS** alıb. Hər arm-ın yeganə PASS-i həmin bug-dur: **clean PASS 0/7**. Genuine allowed-change PASS əldə olunmayıb.

Aggregate counts eyni olsa da **pair-level qərarlar 10/12-də eynidir**: booth **vr_d07179d5 C FAIL / B REVIEW**, frozen-clean **vr_ef9b073a C REVIEW / B FAIL**. C-də 4 FAIL-in 3-ü frozen bug, 1-i frozen clean-dir; B-də 2 bug və 2 clean FAIL-dir. Frozen-clean **vr_43773eb8** hər ikisində FAIL alır; actual subtitle absence ilə frozen A1 label arasında scope conflict var və scoring-də false-FAIL saxlanılır. [C2 report](../CELAL_C2_OPENROUTER_PILOT.md).

| C2 runtime məlumatı | Dəyər | Sübut statusu |
|---|---|---|
| Model / provider / prompt | OpenRouter / google/gemini-3.5-flash / v9 / reasoning low | Raw identities və config ilə **verified** |
| Inputs / rules / policy | Same dev12 və inventory rules; frozen policy | Raw IDs/identity/config independently checked. Exact inventory rules və labels-in prompts-a verilməməsi **Celal report + implementation provenance**-dir; full request/image capture audit pending |
| Calls / retries | 80 fresh calls / 0 cache hits / 0 retries / HTTP 200 80/80 | Calls + stages **independently verified**; inference burada rerun edilməyib |
| Total cost | $0.2871945 (slaydda təxminən $0.287) | Per-call **provider-reported usage cost** Decimal ilə recompute edilib; invoice independently verified deyil |
| Call/cost split | C 56 / $0.1934625; B 24 / $0.0937320 | Per-call records-dan verified |
| Pinned current tests | **194 passed, 6 skipped, 5.14 s** | QA exact delivery checkout-da actual .venv pytest execution |
| Historical C2 tests | **186 passed, 6 deselected, 0 skipped** | Celalın C2 execution report-u; current test run deyil |
| C evidence ZIPs / scans | 12 verification records, Celal host-da checks | Records raw IDs ilə match; **actual ZIP bytes Ali host-da absent**, local unzip/download verified deyil |
| Final integration SHA / C config hash | 79a0ef740196cbaa0639579386c6c591d2bfd8ca / eaa371255716 | Exact fetched checkpoint və identity verified |
| B diagnostic config hash | 2dfeb64cd673 | Same settings, ayrı output/cache namespace |
| C2 barrel run / timing | 20261009T123704Z-8e4e19; wall 31.520 s / pipeline 30.2167 s | C raw row; Celal host n=1; UI timing deyil |
| UI-ready SHA | Pending, Celal ayrıca göndərəcək | Recording gate açılmayıb |

Pitch cümləsi: “12 development pair-də daha güclü VLM ilə hybrid **3/5 bug-a FAIL** verir; coverage **5/12**, bug false-PASS **1/5**-dir. Qwen hybrid **0/12 coverage, 0/5 false-PASS** ilə hamısında abstain edir. Gemini B və C aggregate counts-u eynidir; bu diagnostic-də DINOv2-hybrid advantage sübut edilməyib.”

Coverage artımı false-PASS və clean false-FAIL riskini də gətirir; təhlükəsizlik və ya ümumi accuracy zəmanəti deyil. Bu dev comparison-dan generalization və QA-workload claim-i çıxmır. Stronger model bəzi bug-larda useful FAIL gətirib, perception və coverage problemləri qalır.

Identity mənbələri: [C identity](../c2_openrouter/C_identity.json), [B identity](../c2_openrouter/B_identity.json), [usage records](../c2_openrouter/calls.jsonl), [stages](../c2_openrouter/stages.jsonl), [ZIP verification records](../c2_openrouter/zip-verification.json). Historical C2 execution SHA **c917532ac3161a0886f626985c53307eb2d477d8**, C3 implementation freeze SHA **bdd93fb534e8c0e9b574e60d383bc8b14dd03bf3**, final delivery **79a0ef740196cbaa0639579386c6c591d2bfd8ca** ayrı identities-dir. [Freeze](../FINAL_IMPLEMENTATION_FREEZE.md). B raw helper AnalysisResult ZIP yaratmır; B üçün native ZIP claim-i yoxdur.

## 2. Konkret barrel FAIL: C1 fallback, Qwen REVIEW ilə yanaşı

[Celal C1 gate](../CELAL_C1_DEMO_GATE.md) bir selected dev bug-un fresh end-to-end nəticəsini sənədləşdirir. C1 **Google OpenAI-compatible endpoint** istifadə edib; C2 OpenRouter batch metric-i deyil.

| Field | C1 Gemini barrel | Qwen A1 baseline, eyni pair |
|---|---|---|
| Sample | vr_4b921c5d | vr_4b921c5d |
| run_id | 20261009T115633Z-83936b | 20261009T112802Z-c4530d |
| Model / prompt / config hash | gemini-3.5-flash / v9 / 6cfbba559386 | qwen2.5vl:3b / v9 / 3a144cfcbb67 |
| Region | R1 [2484,1400,3049,1966], source=union | Eyni R1 box |
| Observation | Barrel disappeared, stand empty | Texture / lighting kimi yanlış təsvir |
| Region / final | forbidden / D1 → **FAIL: R1 (D1)** | uncertain → **NEEDS_REVIEW** |
| Scene audit | uncertain; reliable region FAIL qalır | Yanlış allowed; region uncertainty PASS-i bloklayır |
| Verification | **Celal host-da** fresh CLI, browser saved replay və ZIP download verified | [Raw C rows](a1_evidence/predictions_C.jsonl), [Ali browser check](UI_BROWSER_CHECK.md) |

C1: **4 live calls**, retries 0; **CLI wall 25.4442 s**, **pipeline 18.4305 s**, n=1 — Celalın measured values. C1 archive Ali host-da yoxlanmayıb; local replay/download verified claim-i edilmir. Saved run-un ekranda göstərilməsi **REPLAY**-dir. Bir selected dev demo uğuru model accuracy ölçüsü deyil.

## 3. Qwen A1/A3 baseline — verified counts

Local Ollama **qwen2.5vl:3b** (CPU), prompt **v9**, temperature 0. A1 config **configs/ali_a1_qwen.yaml**, hash **3a144cfcbb67**; A3 config **configs/ali_a3_qwen.yaml**, hash **642b6e26f39d**. Config yalnız dump tag və cache namespace ilə fərqlənir. [Registry](EXPERIMENT_REGISTRY.md), [A3 integrity](A3_review.md).

| Arm | PASS / FAIL / REVIEW | Bug false-PASS | Coverage | Clean PASS |
|---|---|---|---|---|
| A pixel (dev-tuned threshold 0.782) | 12 / 0 / 0 | 5/5 | 12/12 | 7/7 |
| B full-frame VLM | 8 / 0 / 4 | 5/5 | 8/12 | 3/7 |
| C hybrid | 0 / 0 / 12 | 0/5 | 0/12 | 0/7 |

Mənbə: [A1 diagnostic](A1_diagnostic.md), [raw score](a1_evidence/score_raw.md), [A3 independent recompute](A3_review.md). Qwen hybrid **safe but abstains**: false-PASS **0/5**, coverage **0/12**; 12/12 REVIEW. **9/12 global-change collapse**, hamısı cutscene. Üç Unity bug-da localization var, perception səhvləri və guards REVIEW yaradır.

A3 A1-i **36/36 rows** üzrə təkrarlayıb; stage-1 text **24/24 VLM rows** üzrə eynidir. A3 **80 fresh calls, 0 cache hits** ilə işləyib. Bu eyni 12 pair və eyni host-da **determinism / regression check**-dir; ikinci sample və ya ikinci accuracy measurement deyil. Effective n=12 qalır. [A3 determinism](A3_review.md).

Sensitivity: ambiguous **vr_330651ed** clean sayılsa 4 bug / 8 clean olur. A false-PASS **4/4**, coverage **12/12**; B **4/4**, coverage **8/12**; C **0/4**, coverage **0/12**. Nəticə dəyişmir. Bu pair-də subtitle language dəyişib; cutscene rules text change-i ayrıca əhatə etmir. [Label audit](labels_audit.md).

## 4. AI və code-un ayrı rolları

Frozen **DINOv2 ViT-S/14** alignment-dən sonra reference/candidate spatial patch distances çıxarır; pixel-diff proposals ilə region crops seçilir. Bu operational localization-dır, bug probability və final verdict deyil. Max 8 regions; global-change collapse full-frame region və truncated=True yaradır. Box **[x1,y1,x2,y2]** original reference pixels-dədir, right/bottom exclusive. [A3 visual review](A3_review.md).

VLM **two-stage** işləyir: stage 1 BEFORE/AFTER composite-dən observation çıxarır, **rules və labels prompt-a daxil edilmir**; stage 2 observation + rules-dan allowed / forbidden / uncertain, rule IDs və evidence verir. Whole-scene audit də two-stage-dir. Labels inference-in heç bir mərhələsinə verilmir. Report model mətnini **VLM-reported, unverified** kimi saxlayır. Implementation: vision/prompts.py, VLMJudge._two_stage().

**decision.decide() deterministic code**-dur: reliable forbidden evidence → **FAIL**; bütün yoxlamalar tamamlanıb allowed olduqda → **PASS**; uncertainty, invalid output, mock, error, bad alignment və truncation reliable FAIL yoxdursa → **NEEDS_REVIEW**. C1-də uncertain scene audit reliable R1/D1 FAIL-i ləğv etmir. PASS heuristic-dir, bütün bug-ların yoxluğunun sübutu deyil.

Barrel/booth proposal boxes labels ilə uyğun gəlir (QA IoU **0.60 / 0.71**); labels abs-diff inspection-dən sonra assistant correction ilə dəyişdiyi üçün bu **tam independent localization evidence deyil**. Pedestal proposals **classical**-dır; onları DINOv2 detection kimi təqdim etmək olmaz. [A3 visual review](A3_review.md), [provenance](labels_audit.md).

Ali-nin one-rater observation marks-ı: B **y+p 4/12**, C **y+p 9/12**; strict y **1/12 hər ikisində**. Partial credit, possible anchoring, n=12; A1 text-də scored-dir, A3-də text identity ilə carry-over olur. Region crops perception-a kömək edən signal verir; automatic decision advantage və ya DINOv2 superiority sübut etmir. [Marks](a1_evidence/obs_review.csv), [A3 caveats](A3_review.md).

## 5. Qorunan failure və limitations

Əsas failure **missing stone pedestal vr_c1f47c57**-dir: reference-də statue altında pedestal var, candidate-də yoxdur; **D1 qalır**. [Pedestal zoom](a3_evidence/vr_c1f47c57_pedestal_zoom_ref_vs_cand.png). Qwen A3 C **REVIEW**, run **20261009T121824Z-157529**. **C2 B/C PASS raw rows-dan verified**-dir; C run **20261009T124621Z-0b0c2b**. Allowed-change success kimi deyil, yanlış avtomatik təsdiq kimi göstərilir.

Qwen hybrid və C2 B/C genuine clean PASS verməyib (**0/7**, verified). Same-crop Gemini reproducer barrel və booth-u **2/2** düzgün təsvir edib; **n=2 reproducer**, accuracy measurement deyil. [Reproducer](a1_evidence/stage1_qwen_vs_gemini.json).

Data **VideoGameQA-Bench, CC BY 4.0**, pinned revision **2afbfdcc9cb84318845f348c023bb2e92b942e29**; manifest-lər dəyişdirilmir. dev12 labels exposed-dur, Unity source yalnız bug-lardan ibarətdir. Historical eval60 bu build-in evaluation-u deyil. Held-out generalization, QA workload reduction və live latency distribution ölçülməyib. [Project brief](../PROJECT_BRIEF.md), [A3 limitations](A3_review.md).

## 6. Qalan verification və təhvil gate

Tamamlanan gate: [raw predictions və calls recompute](C2_RECOMPUTED.json), frozen-label counts, B/C pairwise differences, config/model identity, per-call freshness/cost və exact pinned checkout-da tests. Qalan gate: actual ignored C2 ZIP binaries-in transfer/unzip/hash check-i, full input/request/image capture audit; **UI-ready SHA**, browser saved replay və UI-exported evidence.json; final video duration, second-device acceptance və 19:30 submission confirmation. Celalın ZIP verification records-u local actual archive check-i əvəz etmir.

**17:30-dan sonra yeni feature, experiment və threshold tuning yoxdur.** Video/slides 18:45; acceptance 19:15; daxili submission **19:30**, rəsmi deadline 20:00 Asia/Baku. **Recording UI-ready SHA gələnədək gözləyir**; Qwen vision-branch UI istifadə edilmir. Final code freeze SHA ayrıca saxlanılır. [Task list](NEXT_TASKS.md).

Wording: “development diagnostic on 12 pairs”, “safe but abstains”, “localization works, perception is the bottleneck”, “a stronger model is the evidenced next step”. Sonrakı pilot fresh pre-labelled held-out scene groups və DINOv2 contribution üçün ayrıca ablation-dır; bu gün run edilmir. “Fine-tuned”, “production-ready”, “reduces QA workload”, “DINOv2 beats …” və generalization claim-ləri yoxdur.
