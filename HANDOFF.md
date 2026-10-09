# HANDOFF — Rule-Aware Visual Regression Prototype

**Tarix:** 9 oktyabr 2026 · **Yığan:** senior-pm · **Dil:** Azərbaycan dili, English technical terms
**Qısa nəticə:** end-to-end prototype **real AI ilə işləyir** (real DINOv2 + real VLM, qərar siyasəti, report export, reference history). Amma **detector kimi zəifdir**: 60 held-out pair-də nəticə chance səviyyəsindədir. Hipotez ("DINOv2 proposals VLM-ə kömək edir") bu operating point-də **NOT SUPPORTED**-dir. Sistem hazırda "konservativ triage" kimi davranır: bug-ı nadir hallarda PASS edir, amma pair-lərin ~97%-ni NEEDS REVIEW-a göndərir.

Etiketlər: **VERIFIED** = komanda həqiqətən işlədilib və nəticəsi artifact və ya status faylında var. **UNVERIFIED** = heç kim işlətməyib.

Ətraflı sənədlər: `README.md`, `docs/DEMO_RUNBOOK.md`, `docs/CODE_WALKTHROUGH.md`, `docs/QA_REPORT.md`, `docs/EXPERIMENTS.md`, `docs/DATA_CARD.md`, `docs/MODEL_NOTES.md`, `docs/DECISIONS.md` (D1–D13), `THIRD_PARTY_NOTICES.md`.

---

## 1. Nə işləyir, nə partial, nə yoxdur?

**İşləyir (VERIFIED):**
- Tam axın: reference + candidate + rules → alignment → DINOv2 + classical proposals → crop-lar → hər region üçün VLM judgment → whole-scene audit → deterministic `PASS / FAIL / NEEDS_REVIEW` → `artifacts/<run_id>/` (analysis.json, report.md, crops, ZIP) → explicit "approve as new reference" (versiyalar + `history.json`).
- Real modellər:
  - DINOv2 `dinov2_vits14` CUDA-da işləyir (fp32).
  - VLM `qwen2.5vl:3b` Ollama ilə **CPU**-da işləyir, çünki 6 GB GPU-ya sığmır (D10).
- Qərar siyasəti mərkəzidir (`src/gameqa/decision.py`):
  - error, timeout, mock, truncation, uncompared border və ya unreliable alignment heç vaxt PASS vermir;
  - sübut olunmuş FAIL heç bir component xətası ilə PASS-a çevrilmir.
- Testlər: `.venv/bin/python -m pytest -q` → **168 passed, 6 skipped**. 6 skip `real_model` testləridir; `GAMEQA_REAL=1` ilə QA onları da işlədib: 6 passed, VLM cavabları cache-dən gəlib.
- Data: VideoGameQA-Bench visual-regression subset-in 250 pair-i endirilib (revision `2afbfdcc…`). Manifest-lər leak-free-dir: label-lar yalnız `data/manifests/eval_labels.json`-dadır.
- Fresh process-dən Streamlit launch işləyir (health `ok`, HTTP 200).
- Headless UI smoke (`scripts/ui_smoke.py`, real engine) keçib: Analyze → FAIL göstərilir, rerun inference-i təkrar etmir, approve v1+v2 + history yaradır.

**Partial:**
- **Real brauzerdə klik-klik UI yoxlanmayıb** (Chrome extension qoşulmamışdı). UI yalnız Streamlit `AppTest` ilə yoxlanıb.
- Upload yolu UI-da test olunmayıb. Demo pair yolu test olunub; upload pipeline səviyyəsində test olunub.
- Detector keyfiyyəti zəifdir (bölmə 6).
- Whole-scene audit 3B modeldə etibarsızdır.

**Yoxdur / işlədilməyib:**
- E2b ablation (classical-only proposals + VLM).
- E3 proposal recall (manual region annotation tələb edir).
- Daha güclü VLM ilə müqayisə.

## 2. Setup və run (actual verified commands)

```bash
# Environment (D1): Python 3.13 venv, sistem torch-u istifadə edir
python3 -m venv --system-site-packages .venv          # VERIFIED (hour 0)
.venv/bin/pip install streamlit                       # VERIFIED
.venv/bin/pip install -e . --no-deps                  # VERIFIED
ollama pull qwen2.5vl:3b                              # VERIFIED (Ollama v0.21, localhost:11434)

# Tests
.venv/bin/python -m pytest -q                         # VERIFIED: 168 passed, 6 skipped
GAMEQA_REAL=1 .venv/bin/python -m pytest -q -m real_model   # VERIFIED (QA): 6 passed

# UI
.venv/bin/streamlit run app.py                        # VERIFIED: launch + health; real browser clicks UNVERIFIED
.venv/bin/python scripts/ui_smoke.py object_removed   # VERIFIED: headless UI flow, real engines

# CLI
.venv/bin/python -m gameqa.cli analyze --reference R.png --candidate C.png --rules rules.yaml [--sample-id ID] [--json] [--mock timeout]
.venv/bin/python -m gameqa.cli batch --split demo --out artifacts/demo/demo_split.jsonl          # VERIFIED
.venv/bin/python -m gameqa.cli approve --reference-id ID --run-id RUN [--force]                  # VERIFIED

# Data (yalnız lazım olsa; artıq diskdədir)
.venv/bin/python scripts/prepare_data.py              # VERIFIED (DATA agent), idempotent

# Evaluation
.venv/bin/python scripts/evaluate.py predict --method pipeline --ids-file data/manifests/eval_subset_60.json --out artifacts/eval/<name>
.venv/bin/python scripts/evaluate.py score --run artifacts/eval/<name>
.venv/bin/python scripts/compare_runs.py               # paired bootstrap E1/E2/E4
```

**Vacib əməliyyat qeydləri:**
- Ollama VLM yüklənmə zamanı **~9.3 GiB boş RAM** istəyir. Alınmasa, brauzeri bağla və `ollama stop qwen2.5vl:3b` et. Eyni anda iki VLM işi işlətmə.
- Gecikmə: cache-siz bir pair median ~70 s (p90 ~240 s) çəkir. VLM cavabları `data/cache/vlm/`-də cache olunur; cache-dən gələn run 3–9 s çəkir.
- API key lazım deyil. Cloud key-lər expired və ya placeholder idi (D2).

## 3. Demo: hansı pair-lər, gözlənilən behavior

Hamısı UI-da **Pair source → Demo pair** ilə seçilir və ya CLI ilə işlədilir. Fixture-lər **SYNTHETIC**-dir (əl ilə çəkilib) və benchmark nəticəsi deyil.

| Hal | Pair | Real nəticə (VERIFIED run) |
|---|---|---|
| Forbidden | `data/fixtures/object_removed` | **FAIL**: R1 `forbidden D1` (barrel yox olub). Run `20261008T230730Z-818bb9` |
| Allowed | `data/fixtures/clothing_color_change` | **PASS**: 0 proposal, scene audit `allowed A2`. Run `20261009T065807Z-0f8434` |
| Uncertain | `data/fixtures/lighting_change` | **NEEDS_REVIEW**: R1 `uncertain` |
| Error yolu | istənilən pair + `--mock timeout` | **NEEDS_REVIEW [MOCK]**, səbəb mətnində timeout görünür |
| Əlavə | `allowed_and_forbidden` → FAIL; `small_object_removed` (12 px coin) → FAIL; `identical` → PASS (deterministic shortcut) | |
| Real benchmark | `demo` split-in 5 pair-i (`vr_73635d70`, `vr_536596f0`, `vr_2ada9903`, `vr_b5647b43`, `vr_9aa8a337`) | 5/5 **NEEDS_REVIEW**, hər biri 75–262 s (`artifacts/demo/demo_split.jsonl`) |

Demo zamanı göstər:
- region box-ları və crop-ları;
- verdict, rule ID və evidence;
- engine banner (real / degraded / MOCK);
- **Export bug report (ZIP)**;
- **Approve as new reference**. Run real PASS deyilsə, əlavə "override" checkbox tələb olunur.

## 4. Screenshot-dan verdict-ə actual code path

`src/gameqa/pipeline.py: analyze()`. Ətraflı izahat `docs/CODE_WALKTHROUGH.md`-dədir; orada real run izlənib.

1. `imageio`: decode, ölçü/format limitləri, sha256.
2. `vision/alignment.py: align()`:
   - eyni ölçüdə identity, lazım olduqda translation/affine (quality check-lərlə);
   - pis hallarda `UNRELIABLE`.
   - Overlap xaricindəki piksellər müqayisə olunmur.
3. `vision/features.py: FeatureExtractor.distance_map()`: DINOv2 patch features, `1 - cosine`, reference koordinatlarına geri map olunur.
4. `vision/proposals.py: propose()`:
   - DINOv2 threshold + classical pixel diff, union, merge, padding, max 8 region;
   - qlobal dəyişiklikdə bir full-frame region və `truncated=True`.
5. Crop-lar eyni reference box ilə hər iki şəkildən kəsilir (`[x1,y1,x2,y2]`, right/bottom exclusive).
6. `vision/judge.py: Judge.judge_region()`:
   - prompt v9 tək BEFORE|AFTER composite şəkil göndərir;
   - **stage 1** dəyişikliyi qaydalarsız təsvir edir, **stage 2** text-only olaraq qaydalara görə verdict verir;
   - `validate_response` schema-nı, rule ID-ləri və ziddiyyətləri yoxlayır.
7. `Judge.audit_scene()`: whole-scene audit; proposal-ların buraxdığı dəyişikliklər üçündür.
8. `decision.decide()`: **yeganə qərar yeri**.
   - Reliable forbidden → FAIL. "Reliable" o deməkdir ki, cavab real, validated, evidence ilə, naməlum rule ID olmadan və konfliktsiz deny rule ilə verilib (D6, D9).
   - Alignment etibarsızdırsa, FAIL-ı yalnız audit verə bilər.
   - Overlap < 0.98 olduqda PASS yoxdur (D13).
   - Qalan bütün qeyri-müəyyənliklər NEEDS_REVIEW verir.
9. `storage.py`: atomic write, `export_report`, `approve_reference` (köhnə versiyalar qorunur, audit event yazılır).

## 5. Nəyi harada dəyişmək

| Nə | Harada |
|---|---|
| VLM modeli, timeout, attempt, şəkil ölçüləri | `configs/default.yaml` → `vlm.*` |
| Yeni VLM provider (cloud) | `src/gameqa/vision/judge.py` → `_ollama_reply` yanına yeni metod + `vlm.provider` |
| Prompt-lar | `src/gameqa/vision/prompts.py`. Dəyişəndə `PROMPT_VERSION`-u artır (cache key-in hissəsidir) |
| Cavab validasiyası | `judge.validate_response` |
| DINOv2 threshold, classical threshold, min area, region cap, global-change collapse | `configs/default.yaml` → `proposals.*` (yalnız **dev** split-də tune et) |
| Alignment limitləri | `configs/default.yaml` → `alignment.*` |
| Deadline | `configs/default.yaml` → `run.deadline_s` |
| Qərar siyasəti | `src/gameqa/decision.py` + `tests/policy/test_decision.py` + `docs/DECISIONS.md` |
| Rules | UI cədvəli, `configs/rules_example.yaml` (A1/A2/D1/D2), benchmark üçün `src/gameqa/data/manifest.py: rules_from_question` (D8) |
| Müvəqqəti override | CLI `--config extra.yaml` (default.yaml üstünə merge olunur) |

Default dəyişən hər şeyi `docs/DECISIONS.md`-ə yaz.

## 6. Həqiqətən işlədilən testlər və eksperimentlər

**Testlər:** 168 passed, 6 skipped (pytest). Real-model testləri 6 passed (QA). Code review (`code-reviewer`) heç bir blocker tapmayıb: error→PASS yolu və label leakage yoxdur.

**Eksperimentlər:** eyni 60 held-out eval pair (42 bug / 18 no_bug), dondurulmuş config (`config_hash 8e6c97c0395c`, prompt v9). Əsas metrik balanced accuracy-dir (NEEDS_REVIEW → FAIL kimi sayılır).

| Metod | PASS / FAIL / REVIEW | Balanced acc. (95% CI) | False PASS (bug → PASS) | Review rate |
|---|---|---|---|---|
| E1 classical pixel-diff (dev-də tune, D12) | 58 / 2 / 0 | 0.524 [0.500, 0.560] | 40/42 | 0% |
| **E2 pipeline (DINOv2 + VLM)** | 1 / 1 / 58 | 0.488 [0.464, 0.500] | **1/42** | 96.7% |
| E4 yalnız VLM (whole-scene) | 43 / 0 / 17 | 0.385 [0.254, 0.516] | **33/42** | 28.3% |

- E1 full eval split-də (205 pair) BA 0.516-dır.
- **Verdikt:** hipotez **NOT SUPPORTED**. E2 E1-dən yaxşı deyil: paired diff −0.036, CI [−0.083, 0.000].
- E2-nin aşağı false PASS-ı əsasən **abstention**-dan gəlir: 60 run-ın 53-ü truncated idi (37 global-change collapse, 16 region cap).
- Proposals + strict validation false PASS-ı 33/42-dən (E4) 1/42-yə (E2) endirir. Fərq McNemar testi ilə əhəmiyyətlidir (p≈5e-10), amma bunun bahası çox yüksək review rate-dir.
- **Confound-lar:**
  - bütün Unity pair-lər bug-dır, no_bug yalnız cutscene-dədir;
  - benchmark-da cəmi 2 fərqli question text var;
  - N kiçikdir.

  Bu, smoke test-dir, significance testi deyil.
- Ətraflı: `docs/EXPERIMENTS.md`, `artifacts/eval/*/metrics.md`, `artifacts/eval/paired_comparison.json`.

## 7. Ən vacib known failure və onu reproduce etmək

**Dangerous false PASS: `vr_bcbcf341` (Unity, label = bug).**
- **Nə baş verib:** candidate-də yolun teksturu itib, yer qaranlıq və düz görünür.
- **Lokalizasiya düzgündür:** DINOv2 + classical proposal `R1 [1213,1973,3003,2160]` dəyişiklik zonasını əhatə edir.
- **VLM səhv mühakimə edib:**
  - region judgment: "license plate more visible" → `allowed A1`;
  - scene audit: "brighter lighting" → `allowed A1`.
  - İkisi də validated olduğu üçün `decide()` PASS verdi.
- **Səbəb:** siyasət dizayn olunduğu kimi işləyib; problem 3B VLM-in mühakimə keyfiyyətidir. Eval label-ı ilə tuning etmədik, çünki bu protokolu pozardı.

```bash
.venv/bin/python -m gameqa.cli analyze \
  --reference data/work/vr_bcbcf341/reference.png \
  --candidate data/work/vr_bcbcf341/candidate.png \
  --rules artifacts/20261009T003250Z-58905e/rules.yaml --sample-id vr_bcbcf341
# Gözlənilən (QA reproduce edib, cache-dən): Decision PASS, R1 allowed A1
```

Saxlanan run: `artifacts/20261009T003250Z-58905e/` (`report.md`, `crops/R1_ref.png`, `crops/R1_cand.png`).

**Digər məlum problemlər:**
1. **Review rate ~97%.** Cutscene pair-lər `no_bug` olsa da qlobal fərqlənir, ona görə global-change collapse işə düşür → truncated → NEEDS_REVIEW.
2. **Kiçik obyektlər.** 12 px coin DINOv2-də threshold sərhədindədir və yalnız classical fallback tutur.
3. **Proposal yaranmayan dəyişikliklər.** Kiçik rəng dəyişikliyi kimi hallarda qərar yalnız scene audit-ə qalır. `vr_bcbcf341`-dəki kimi səhv PASS riski buradan gəlir.
4. **Açıq minor defect-lər (`docs/QA_REPORT.md`):**
   - QA-D12: mock provider + pixel-identical audit shortcut `mock` engine ilə PASS verə bilir.
   - QA-D13: judge exception real/COMPLETE kimi etiketlənir.
   - QA-D14: "no visible change" cavabı rule ID olmadan allowed sayılır.
   - QA-D15: E2 `run_meta`-dakı commit sahəsi düz deyil; etibarlı identity `config_hash`-dır.
5. **E2 və D13:** E2 artifact-ləri D13 düzəlişlərindən əvvəl yaradılıb (`artifacts/` git-də deyil, lokal diskdədir). D13 nəticələri dəyişmir: bütün E2 run-larının overlap ≥ 0.98-dir və provider error yoxdur.

## 8. Data, model və lisenziya

- **Data:** `taesiri/VideoGameQA-Bench`, revision `2afbfdcc9cb84318845f348c023bb2e92b942e29`, **CC BY 4.0**.
  - 250 visual-regression pair (171 Unity + 79 cutscene; 224 bug / 26 no_bug).
  - Yalnız metadata + seçilmiş şəkillər endirilib (~0.7 GB raw); 33.4 GB-ın hamısı yox.
  - Split (seed 13, bizim daxili protokolumuz, rəsmi split deyil): demo 5 / dev 40 / eval 205.
  - Ətraflı: `docs/DATA_CARD.md`.
- **Modellər:**
  - DINOv2 ViT-S/14 (Apache-2.0, `torch.hub` `facebookresearch/dinov2@main`, weights sha256 `b938bf1bc15c…`).
  - `qwen2.5vl:3b` Q4_K_M via Ollama. Lisenziya **non-commercial (Qwen Research License) kimi qəbul edilib**, yoxlanana qədər.
  - Ətraflı: `THIRD_PARTY_NOTICES.md`, `docs/MODEL_NOTES.md`.

## 9. Git checkpoint

Branch `master`, yalnız lokal (remote yoxdur). Commit-lər: `9c09345` (skeleton) → `0b3cc1b` (vertical slice) → `c463a07` (real inference, config E2-dən əvvəl donduruldu) → `1f81dd2` → final handoff commit (`git log -1`). Data (`data/raw`, `data/work`), `artifacts/` və `references/` git-də deyil, lokal diskdədir. Manifest-lər və fixture-lər commit olunub.

## 10. Ali-nin sabah ilk üç işi

1. **Real brauzerdə demo-nu keç (30 dəq).**
   - `.venv/bin/streamlit run app.py`; bölmə 3-dəki üç demo case-i (`object_removed`, `clothing_color_change`, `lighting_change`) aç.
   - Export ZIP-i yoxla, approve-u et.
   - Bu, hələ VERIFIED olmayan yeganə P0 bəndidir. Problem görsən, `app.py` + `tests/app/test_app.py`.
2. **Daha güclü VLM ilə hipotezi ədalətli yoxla.**
   - İşləyən bir API key (cloud) və ya GPU-ya sığan model ilə `judge.py`-yə provider əlavə et.
   - Əvvəl **dev** split-də 10 pair-də validated `forbidden`/`allowed` sayını və latency-ni ölç.
   - Sonra eyni `eval_subset_60.json` üzərində E2-ni təkrarla: `scripts/evaluate.py predict ... --config <new>.yaml`, sonra `score`, sonra `compare_runs.py`.
   - 3B model bütün testi məhdudlaşdırır; bu, ən böyük lever-dir.
3. **Review rate-i azalt, false PASS-ı artırmadan.**
   - Yalnız dev split-də `proposals.global_change_fraction` (0.10) və `max_regions` (8) ilə oyna.
   - Paralel olaraq `vr_bcbcf341` tipli səhvlərə qarşı qayda düşün: DINOv2 məsafəsi yüksəkdir, amma VLM yalnız "lighting/visibility" deyirsə → review. Bu, `decision.py`-də olmalıdır, `DECISIONS.md` qeydi və test ilə.
   - Eval split-ə baxmadan qərar ver, sonra E2b ablation-ı da işlət.
