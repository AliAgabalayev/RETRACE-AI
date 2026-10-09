# HANDOFF (qaralama, faza 2) - documentation-engineer

Qeyd: bu qaralamadır (faza 3, final); yekun `HANDOFF.md`-ni senior-pm yığır. "VERIFIED" = status faylı, QA_REPORT, senior-pm və ya mənim özümün işlətdiyim komanda təsdiq edib. "UNVERIFIED" = hələ heç kim işlətməyib. qa-engineer-in real-model testləri bu qaralama yazılanda hələ gedirdi; onların nəticəsi burada YOXDUR.

## 1. Nə işləyir, nə partial-dır?
- İşləyir (VERIFIED): `.venv/bin/python -m pytest -q` -> 164 passed, 6 skipped (senior-pm; mən də işlətdim, 5.0 s). 6 skipped = `GAMEQA_REAL=1` ilə açılan `real_model` testləri.
- İşləyir (VERIFIED, senior-pm, real DINOv2 + real `qwen2.5vl:3b`, SYNTHETIC fixture, `gameqa.cli analyze`): `object_removed` -> FAIL, `allowed_and_forbidden` -> FAIL, `small_object_removed` -> FAIL (run `20261009T065813Z-43cffa`), `clothing_color_change` -> PASS (0 proposal, scene audit `allowed A2`; run `20261009T065807Z-0f8434`; artifact-i mən oxudum), `lighting_change` -> NEEDS_REVIEW, `identical` -> PASS (deterministic shortcut, VLM-siz; run `20261009T065816Z-3054be`). Hamısı `real / complete`. Bəzi VLM cavabları disk cache-dən gəlib (latency 0.0); cache-siz pair median ~70 s çəkir (CPU).
- İşləyir (VERIFIED, mən): CLI `--mock timeout|allowed` -> `NEEDS_REVIEW [MOCK]`; `approve` -> `references/<id>/versions/v1.png, v2.png` + `history.json`.
- İşləyir (VERIFIED, senior-pm): benchmark `demo` split, `batch --split demo --out artifacts/demo/demo_split.jsonl`: 5 pair-in hamısı NEEDS_REVIEW, `real / complete`, hər biri 75-262 s (bax bölmə 6).
- UI: VERIFIED yalnız headless: `scripts/ui_smoke.py` (Streamlit `AppTest`, real engine) keçdi: Analyze -> FAIL göründü, rerun inference-i təkrar etmədi, approve -> v1+v2+`history.json`. VLM cavabları əvvəlki real run-ın disk cache-indən gəlib. **Real brauzerdə klik-klik yoxlama VERIFIED DEYİL** (Chrome extension qoşulmayıb).
- Zəif: whole-scene audit (3B model removal-ı bəzən `allowed` adlandırır; `validate_response` bunu rədd edir), qaydaları (rules) xəritələmə, benchmark pair-lərdə recall (E2-də 42 bug-dan 1 FAIL tutulub, bax bölmə 6).
- Nəticə: sistem "konservativ triage" kimi işləyir (nadir hallarda bug-ı PASS edir, amma pair-lərin ~97 %-ni review-ya atır). Hipotez NOT SUPPORTED (bölmə 6).

## 2. Setup/run (hamısı `README.md`-də)
- VERIFIED: `.venv` (`--system-site-packages`), `pip install streamlit`, `pip install -e . --no-deps`, `ollama pull qwen2.5vl:3b`.
- Test: `.venv/bin/python -m pytest -q`.
- UI: `.venv/bin/streamlit run app.py`.
- CLI: `.venv/bin/python -m gameqa.cli analyze --reference R --candidate C --rules rules.yaml [--mock timeout]`; `batch --split demo`; `approve --reference-id ID --run-id RUN`.
- Ollama VLM CPU-da işləyir (6 GB GPU-ya sığmır). Yüklənmə üçün ~9.3 GiB boş RAM lazımdır; alınmasa brauzeri bağla və `ollama stop qwen2.5vl:3b` et.
- Gizli məlumat yoxdur: lokal setup üçün heç bir API key lazım deyil (cloud key-lər expired idi, D2).

## 3. Demo pair-lər
`docs/DEMO_RUNBOOK.md`. Üç hal: forbidden = `object_removed` (FAIL), allowed = `clothing_color_change` (PASS, real run-da müşahidə olunub, amma bu bir əl ilə çəkilmiş pair-dir, ümumi PASS qabiliyyəti sübutu deyil), uncertain/error = `lighting_change` (NEEDS_REVIEW) + MOCK `timeout` yolu. Bütün fixture-lər SYNTHETIC-dir. Real benchmark `demo` split-də 5 pair var (`vr_73635d70`, `vr_536596f0`, `vr_2ada9903`, `vr_b5647b43`, `vr_9aa8a337`); hamısı NEEDS_REVIEW (bölmə 6).

## 4. Screenshot-dan verdict-ə code path
`docs/CODE_WALKTHROUGH.md` (real `artifacts/20261008T230650Z-1335da` izlənib). Qısa: `analyze()` -> `align()` -> `FeatureExtractor.distance_map()` -> `propose()` -> `Judge.judge_region()` + `Judge.audit_scene()` -> `decide()`.

Rollar: DINOv2 (və classical pixel diff) yalnız "harada fərq var" təklif edir. VLM isə hər təklif olunan region üçün ayrıca "bu dəyişiklik qaydaya görə icazəlidir, qadağandır, yoxsa bilmirəm" deyir. Final qərarı yalnız `decision.decide()` verir, deterministik şəkildə.

Konkret misal (`object_removed`): proposal `R1 [424,181,521,286]` (DINOv2 + classical = `union`) -> VLM stage 1 şəkli təsvir edir ("bir obyekt BEFORE-da var, AFTER-da yoxdur"), stage 2 qaydalara baxır -> `forbidden D1`, `validated=true` -> `decide()`: etibarlı forbidden -> `FAIL`. Whole-scene audit isə `uncertain` qalır (özünə zidd cavab rədd edilib), amma nə FAIL-ı bloklayır, nə də kömək edir.

Niyə xəta `NEEDS_REVIEW` olur: timeout, yanlış JSON, mock, truncation, etibarsız alignment sübut deyil. Heç biri PASS-a çevrilmir; yalnız sübut olunmuş forbidden dəyişiklik FAIL verir.

Əhəmiyyətli siyasət dəyişiklikləri (DECISIONS): D6 (`allowed` yalnız validated, real, evidence ilə və deny rule göstərmədən PASS dəstəkləyir), D9 (naməlum rule ID heç nəyi dəstəkləmir; ziddiyyətli deny rule FAIL vermir; alignment etibarsızdırsa yalnız whole-scene audit FAIL verə bilər), D10 (`vlm.timeout_s` 30 -> 75, prompt v9, global-change collapse).

## 5. Nəyi harada dəyişmək
- Model, timeout, threshold, region cap, deadline: `configs/default.yaml` (açarlar: `vlm.model`, `vlm.timeout_s`, `proposals.dinov2_threshold` 0.35, `proposals.classical_threshold` 40, `proposals.max_regions` 8, `proposals.global_change_fraction` 0.10, `alignment.*`, `run.deadline_s`). Defolt dəyişəndə `docs/DECISIONS.md`-ə yaz.
- Başqa VLM provider: `Judge._ollama_reply` (`judge.py:247`) yanına yeni metod, `provider:` açarı.
- Prompt: `src/gameqa/vision/prompts.py`; dəyişəndə `PROMPT_VERSION` artır (cache key-in hissəsidir). Nümunə cümlə əlavə etmə: 3B model onları kopyalayır.
- Cavab yoxlaması: `judge.validate_response`.
- Final qərar siyasəti: `src/gameqa/decision.py` (testlər `tests/policy/test_decision.py`).
- Rules: UI cədvəli və ya YAML (`configs/rules_example.yaml`); benchmark üçün `data/manifest.py:rules_from_question`.
- Sınaq üçün konfiqi dəyişmədən override: `--config extra.yaml`.
- Prompt versiyası config açarı deyil: `PROMPT_VERSION` (`prompts.py`, v9). `Judge`-in default-ları indi yaml ilə eynidir (D11).
- `approve`: real-engine PASS olmayan run üçün CLI-də `--force`, UI-da əlavə "override" checkbox lazımdır (D11).
- Model yüklənməsi uğursuz olubsa: Streamlit sidebar-da "Reload models" (restart lazım deyil).

## 6. E2 / E4 / E1 nəticələri (senior-pm-in verdiyi faktlar; mənbə `docs/EXPERIMENTS.md` bölmə 6, D11, D12)
Hamısı eyni 60 held-out eval pair-ində (42 bug / 18 no_bug), real DINOv2 + `qwen2.5vl:3b`, prompt v9, dondurulmuş config. Əsas metrik: balanced accuracy (BA), review -> FAIL xəritəsi.

| Metod | PASS / FAIL / REVIEW | BA | Bug-ın PASS olması (false PASS) | Review rate |
| --- | --- | --- | --- | --- |
| E1 classical pixel-diff | 58 / 2 / 0 | 0.524 | 40/42 | 0 % |
| E2 pipeline (DINOv2 + VLM) | 1 / 1 / 58 | 0.488 | **1/42** | 96.7 % |
| E4 yalnız VLM (whole-scene) | 43 / 0 / 17 | 0.385 | **33/42** | 28.3 % |

- **Verdikt (əvvəlcədən elan olunmuş qayda): hipotez NOT SUPPORTED** bu operating point-də (3B VLM, CPU, prompt v9, 60 pair). E2 E1-dən yaxşı deyil (0.488 < 0.524, yuxarı CI sərhədi 0.500).
- E2-nin aşağı false-PASS-ı əsasən **abstention**-dır: 60 run-ın 53-ü `truncated` idi (37 global-change collapse, 16 region cap) və truncation həmişə NEEDS_REVIEW verir. "Həmişə NEEDS_REVIEW" eyni təhlükəsizliyə və BA 0.500-ə malikdir. E2 bunun üstünə 1 düzgün FAIL (`vr_36133e80`) və 1 yanlış PASS (`vr_bcbcf341`) əlavə edir.
- E2b (yalnız classical proposal + VLM) və E3 (proposal recall) İŞLƏDİLMƏYİB, ona görə "DINOv2 proposal-ları kömək edir" iddiası təkbaşına ölçülməyib.
- E1 threshold (D12): əvvəlki split-də tune olunmuşdu (23/37 "dev" ID indi eval-dadır); cari dev split-də (40 ID) yenidən tune olundu: threshold 0.782, dev BA 0.515; nəticələr dəyişmədi, subset60 BA 0.524, full eval BA 0.516. İndi leakage-clean.
- Confound: unity pair-lərin hamısı bug, no_bug yalnız cutscene-dir; yalnız cutscene-də false-positive ölçmək olar (N kiçik: 18 no_bug).
- Benchmark `demo` split (5 pair, real, `artifacts/demo/demo_split.jsonl`, mən oxudum): hamısı NEEDS_REVIEW. Region sayı: `vr_73635d70` 1, `vr_536596f0` 1, `vr_2ada9903` 12 (8-i judge olunub, truncated), `vr_b5647b43` 8, `vr_9aa8a337` 1. Müddət 75-262 s. Bir çox region üçün cavab `validate_response`-dan keçməyib ("invalid or failed model response").
- Pair sayı kiçikdir: bu smoke test-dir, yalnız iri effektləri göstərir.

## 7. Ən vacib known failure-lar (reproduce yolları ilə)
1. **Yanlış PASS: `vr_bcbcf341` (Unity, bug).** Ən təhlükəli nəticə. DINOv2 + classical proposal `R1 [1213,1973,3003,2160]` yolun yerə düşən teksturunun yoxluğunu düzgün əhatə edir; amma VLM bunu "license plate more visible" kimi təsvir etdi -> `allowed A1`, whole-scene audit isə "brighter lighting" dedi -> `allowed A1`. İkisi də validated olduğu üçün `decide()` PASS verdi. Siyasət dizayn olunduğu kimi işlədi; problem VLM-in mühakimə keyfiyyətidir. Bunu tuning ilə düzəltmədik, çünki bu, eval label-dan istifadə etmək olardı. Run saxlanılıb: `artifacts/20261009T003250Z-58905e` (`report.md`, `crops/`, `rules.yaml`). Reproduce (real VLM çağırır, mən təkrar ETMƏMİŞƏM):
   `.venv/bin/python -m gameqa.cli analyze --reference data/work/vr_bcbcf341/reference.png --candidate data/work/vr_bcbcf341/candidate.png --rules artifacts/20261009T003250Z-58905e/rules.yaml --sample-id vr_bcbcf341`
   Növbəti addım: bölmə 9, 1-3-cü maddələr.
2. Çox yüksək review rate (E2: 58/60). Səbəb: global-change collapse (37 run) və region cap (16 run). Cutscene pair-lər `no_bug` olsa belə qlobal fərqlənir -> bir full-frame region, `truncated=true` -> həmişə `NEEDS_REVIEW`. Dev-də threshold və collapse dəyişikliyi eval-a baxmadan edilməlidir.
3. Kiçik obyekt: `small_object_removed` (12 px coin). DINOv2 max distance 0.35 = threshold (etibarsız); classical tutur (real run FAIL, `20261009T065813Z-43cffa`). DINOv2-only miss-i görmək üçün `--config` ilə `proposals.sources: [dinov2]` (UNVERIFIED).
4. Dəyişiklik proposal vermir: `clothing_color_change` heç bir region yaratmır; qərar yalnız scene audit-ə söykənir (real run PASS). Eyni mexanizm `vr_bcbcf341`-də səhv PASS-a gətirə bilər.
5. Alignment həssaslığı: `UNRELIABLE` olanda region-level FAIL söndürülür, yalnız `SCENE` judgment FAIL verə bilər (D9).
6. Kalibrasiya olunmamış 3B verdict-lər: VLM obyektin adını səhv yazır ("brown blocks" vs "barrel"), amma verdict düzgün ola bilər. Self-confidence istifadə olunmur.
7. Latency: CPU-da ~20 s region, ~35 s audit; E2-də median 70 s, mean 116 s, p90 238 s per pair; demo pair-lər 75-262 s.
8. Selective download: yalnız metadata + seçilmiş şəkillər endirilib (33.4 GB-ın hamısı yox); `sha256_*` raw JPEG-dir.

## 8. Doc/code uyğunsuzluqları (bug kimi bax)
Siyahı `docs/READABILITY_FEEDBACK.md` "Mismatches" bölməsindədir. D11 təmizliyindən sonra qalanlar: (a) `docs/QA_REPORT.md` köhnədir (4 skipped, "E2/E4 not run", xfail); (b) `artifacts/20261008T230650Z-1335da` köhnə engine-mode ilə `degraded` yazılıb (eyni pair `20261008T230730Z-818bb9` `real/complete`-dir); (c) D4 `analyze(...)` imzasında `run_dir=` yoxdur; (d) `MOCK_BEHAVIORS` hələ üç yerdə təkrarlanır. Həll olunanlar: `vlm.prompt_version` ölü açarı silindi, `judge` default-ları yaml ilə eynidir, `decision.py` docstring-i D9-u əks etdirir, `SCENE_REGION_ID` ortaq sabitdir, mock timeout səbəbi indi `decide()` mətnində görünür.

## 9. Ali üçün növbəti işlər (prioritet sırası ilə)
1. `vr_bcbcf341` false PASS-ı anla (30 dəq): `artifacts/20261009T003250Z-58905e/report.md` və crop-lara bax. Ölç: eyni R1 crop-u daha güclü VLM-ə ver. Fayllar: `src/gameqa/vision/judge.py`, `configs/default.yaml`. Yoxlama: dev split-də (eval-a toxunmadan) validated `forbidden`/`allowed` düzgünlüyü.
2. "Removal şübhəsi" qaydası: proposal-da DINOv2 mesafəsi yüksəkdirsə və VLM "lighting/brightness/more visible" kimi deyirsə, `allowed` PASS vermək əvəzinə review. Fayl: `src/gameqa/decision.py` (yalnız `docs/DECISIONS.md`-ə yazaraq, `tests/policy/test_decision.py` ilə). Diqqət: bu, review rate-i artırır.
3. Daha güclü VLM (cloud və ya GPU-ya sığan) ilə eyni prompt-ları dev split-də müqayisə et. Fayllar: `judge.py` (`_ollama_reply`), `configs/default.yaml`. Yoxlama: eyni 10 dev pair, validated `forbidden` sayı və timing. Bu, hipotezi ədalətli test etmək üçün ən böyük lever-dir.
4. Review rate-i azalt: global-change collapse threshold-u (`proposals.global_change_fraction` 0.10) və `max_regions` 8-i yalnız dev split-də yoxla; eval split-ə toxunma (protokol qaydası 2). Yoxlama: dev-də review rate və false PASS birlikdə.
5. E2b ablation (classical-only proposal + VLM) işlət ki, "DINOv2 kömək edir" iddiası təkbaşına ölçülsün. Fayl: `scripts/evaluate.py predict`, `configs` ilə `proposals.sources: [classical]`.
6. Small-object recall: `dinov2_threshold` və `classical_threshold`-u yalnız dev split-də yoxla. Yoxlama: `tests/vision` + `small_object_removed`.
7. Real brauzerdə `streamlit run app.py` ilə klik-klik yoxla (VERIFIED deyil), `docs/DEMO_RUNBOOK.md`-dəki addımlarla.
8. Okunaqlılıq düzəlişləri: `docs/READABILITY_FEEDBACK.md`.
