# HANDOFF (qaralama, faza 2) - documentation-engineer

Qeyd: bu qaralamadır; yekun `HANDOFF.md`-ni senior-pm yığır. "VERIFIED" = status faylı, QA_REPORT, senior-pm və ya mənim özümün işlətdiyim komanda təsdiq edib. "UNVERIFIED" = hələ heç kim işlətməyib. "PENDING" = nəticə hələ gəlməyib (E2 gedir).

## 1. Nə işləyir, nə partial-dır?
- İşləyir (VERIFIED): `.venv/bin/python -m pytest -q` -> 163 passed, 6 skipped (senior-pm; mən də işlətdim, 5.5 s). 6 skipped = `GAMEQA_REAL=1` ilə açılan `real_model` testləri.
- İşləyir (VERIFIED, real DINOv2 + real `qwen2.5vl:3b`, SYNTHETIC fixture): `object_removed` -> FAIL (R1 forbidden D1), `allowed_and_forbidden` -> FAIL, `lighting_change` -> NEEDS_REVIEW. Hamısı `real / complete`. Qeyd: `object_removed` run-ı VLM disk cache-dən gəlib (3-4 s); cache-siz bir pair median ~85 s çəkir (CPU).
- İşləyir (VERIFIED, mən): CLI `--mock timeout|allowed` -> `NEEDS_REVIEW [MOCK]`; `approve` -> `references/<id>/versions/v1.png, v2.png` + `history.json`.
- Partial: `clothing_color_change` -> PASS yalnız nəzəridir (dl-engineer: heç bir proposal yoxdur, audit `allowed A2`). End-to-end UNVERIFIED; senior-pm E2-dən sonra işlədəcək.
- Partial: Streamlit UI başlayır (VERIFIED), amma real VLM ilə Analyze düyməsi UI-dan mənim tərəfimdən yoxlanmayıb (CLI eyni `pipeline.analyze`-ı çağırır).
- Zəif: whole-scene audit (3B model removal-ı bəzən `allowed` adlandırır; `validate_response` bunu rədd edir), qaydaları (rules) xəritələmə, benchmark pair-lərdə recall (dev-də 10 pair-in heç birində validated `forbidden` olmayıb).
- E2/E4 nəticələri: bax bölmə 6 (PENDING).

## 2. Setup/run (hamısı `README.md`-də)
- VERIFIED: `.venv` (`--system-site-packages`), `pip install streamlit`, `pip install -e . --no-deps`, `ollama pull qwen2.5vl:3b`.
- Test: `.venv/bin/python -m pytest -q`.
- UI: `.venv/bin/streamlit run app.py`.
- CLI: `.venv/bin/python -m gameqa.cli analyze --reference R --candidate C --rules rules.yaml [--mock timeout]`; `batch --split demo`; `approve --reference-id ID --run-id RUN`.
- Ollama VLM CPU-da işləyir (6 GB GPU-ya sığmır). Yüklənmə üçün ~9.3 GiB boş RAM lazımdır; alınmasa brauzeri bağla və `ollama stop qwen2.5vl:3b` et.
- Gizli məlumat yoxdur: lokal setup üçün heç bir API key lazım deyil (cloud key-lər expired idi, D2).

## 3. Demo pair-lər
`docs/DEMO_RUNBOOK.md`. Üç hal: forbidden = `object_removed` (FAIL), allowed = `clothing_color_change` (UNVERIFIED), uncertain/error = `lighting_change` (NEEDS_REVIEW) + MOCK `timeout` yolu. Bütün fixture-lər SYNTHETIC-dir. Real benchmark `demo` split-də 5 pair var (`vr_73635d70`, `vr_536596f0`, `vr_2ada9903`, `vr_b5647b43`, `vr_9aa8a337`); nəticələri "pending".

## 4. Screenshot-dan verdict-ə code path
`docs/CODE_WALKTHROUGH.md` (real `artifacts/20261008T230650Z-1335da` izlənib). Qısa: `analyze()` -> `align()` -> `FeatureExtractor.distance_map()` -> `propose()` -> `Judge.judge_region()` + `Judge.audit_scene()` -> `decide()`.

Rollar: DINOv2 (və classical pixel diff) yalnız "harada fərq var" təklif edir. VLM isə hər təklif olunan region üçün ayrıca "bu dəyişiklik qaydaya görə icazəlidir, qadağandır, yoxsa bilmirəm" deyir. Final qərarı yalnız `decision.decide()` verir, deterministik şəkildə.

Konkret misal (`object_removed`): proposal `R1 [424,181,521,286]` (DINOv2 + classical = `union`) -> VLM stage 1 şəkli təsvir edir ("bir obyekt BEFORE-da var, AFTER-da yoxdur"), stage 2 qaydalara baxır -> `forbidden D1`, `validated=true` -> `decide()`: etibarlı forbidden -> `FAIL`. Whole-scene audit isə `uncertain` qalır (özünə zidd cavab rədd edilib), amma nə FAIL-ı bloklayır, nə də kömək edir.

Niyə xəta `NEEDS_REVIEW` olur: timeout, yanlış JSON, mock, truncation, etibarsız alignment sübut deyil. Heç biri PASS-a çevrilmir; yalnız sübut olunmuş forbidden dəyişiklik FAIL verir.

Əhəmiyyətli siyasət dəyişiklikləri (DECISIONS): D6 (`allowed` yalnız validated, real, evidence ilə və deny rule göstərmədən PASS dəstəkləyir), D9 (naməlum rule ID heç nəyi dəstəkləmir; ziddiyyətli deny rule FAIL vermir; alignment etibarsızdırsa yalnız whole-scene audit FAIL verə bilər), D10 (`vlm.timeout_s` 30 -> 75, prompt v9, global-change collapse).

## 5. Nəyi harada dəyişmək
- Model, timeout, threshold, region cap, deadline: `configs/default.yaml` (açarlar: `vlm.model`, `vlm.timeout_s`, `proposals.dinov2_threshold` 0.35, `proposals.classical_threshold` 40, `proposals.max_regions` 8, `proposals.global_change_fraction` 0.10, `alignment.*`, `run.deadline_s`). Defolt dəyişəndə `docs/DECISIONS.md`-ə yaz.
- Başqa VLM provider: `Judge._ollama_reply` (`judge.py:262`) yanına yeni metod, `provider:` açarı.
- Prompt: `src/gameqa/vision/prompts.py`; dəyişəndə `PROMPT_VERSION` artır (cache key-in hissəsidir). Nümunə cümlə əlavə etmə: 3B model onları kopyalayır.
- Cavab yoxlaması: `judge.validate_response`.
- Final qərar siyasəti: `src/gameqa/decision.py` (testlər `tests/policy/test_decision.py`).
- Rules: UI cədvəli və ya YAML (`configs/rules_example.yaml`); benchmark üçün `data/manifest.py:rules_from_question`.
- Sınaq üçün konfiqi dəyişmədən override: `--config extra.yaml`.

## 6. E2 / E4 nəticələri (senior-pm dolduracaq) - PENDING
- E2 (pipeline, 60 pair, `artifacts/eval/e2_pipeline_subset60`): PENDING.
- E4 (vlm_only, 60 pair): PENDING.
- E1 classical baseline (VERIFIED, QA): full eval 205 pair, balanced accuracy 0.516 (bug recall 0.03) ~ təsadüf səviyyəsi; subset60: 0.524.
- Hipotez ("DINOv2 proposals VLM-ə kömək edir") hələ ÖLÇÜLMÜYÜB. Nəticə yazılanda: per-source (Unity hamısı bug, no_bug yalnız Cutscene) və review->FAIL xəritəsi ilə balanced accuracy.

## 7. Ən vacib known failure-lar (reproduce yolları ilə)
1. Kiçik obyekt: `small_object_removed` (12 px coin). DINOv2 max distance 0.35 = threshold (etibarsız); classical tutur. Reproduce: fixture + `--config` ilə `proposals.sources: [dinov2]` (UNVERIFIED).
2. Dəyişiklik proposal vermir: `clothing_color_change` heç bir region yaratmır; qərar yalnız scene audit-ə söykənir.
3. Qlobal dəyişiklik: cutscene pair-lər `no_bug` olsa belə qlobal fərqlənir -> bir full-frame region, `truncated=true` -> həmişə `NEEDS_REVIEW` (PASS mümkün deyil).
4. Alignment həssaslığı: `UNRELIABLE` olanda region-level FAIL söndürülür (D9).
5. Kalibrasiya olunmamış 3B verdict-lər: VLM obyektin adını səhv yazır ("brown blocks" vs "barrel"), amma verdict düzgün ola bilər. Self-confidence istifadə olunmur.
6. Latency: CPU-da ~20 s region, ~35 s audit, median ~85 s/pair.
7. Selective download: yalnız metadata + seçilmiş şəkillər endirilib (33.4 GB-ın hamısı yox); `sha256_*` raw JPEG-dir.

## 8. Doc/code uyğunsuzluqları (bug kimi bax)
Siyahı `docs/READABILITY_FEEDBACK.md` "Mismatches" bölməsindədir. Əsasları: `configs/default.yaml:43` `vlm.prompt_version: v1` ölüdür (real versiya `prompts.py:11` = `v9`); `artifacts/20261008T230650Z-1335da` köhnə engine-mode ilə `degraded` yazılıb; `decision.py:1-9` modul docstring-i D9-un alignment qaydasını əks etdirmir; mock `timeout` səbəbi `decide()` mətnində görünmür.

## 9. Ali üçün növbəti işlər (prioritet sırası ilə)
1. E2/E4 nəticələrini oxu (`docs/EXPERIMENTS.md`, `artifacts/eval/*`), hipotez haqqında senior-pm-in tövsiyəsini yoxla. Yoxlama: `scripts/evaluate.py score --run artifacts/eval/e2_pipeline_subset60`.
2. `clothing_color_change`-i real engine ilə işlət (UI və ya CLI). Gözlənti: PASS və ya NEEDS_REVIEW; PASS-dırsa audit `allowed A2` validated olmalıdır. Fayl: `vision/judge.py`, `decision.py`.
3. Daha güclü VLM (cloud və ya GPU-ya sığan) ilə eyni prompt-ları dev split-də müqayisə et. Fayllar: `judge.py` (`_ollama_reply`), `configs/default.yaml`. Yoxlama: eyni 10 dev pair, validated `forbidden` sayı və timing.
4. Small-object recall: `dinov2_threshold` və `classical_threshold`-u yalnız dev split-də yoxla (eval split-ə toxunma). Yoxlama: `tests/vision` + `small_object_removed`.
5. Okunaqlılıq düzəlişləri (`docs/READABILITY_FEEDBACK.md`): ölü config açarı, `judge.py:345` təkrar şərt, `_rule_fields` istifadə olunmayan açarlar.
6. 5 demo benchmark pair-i işlət və `docs/DEMO_RUNBOOK.md` cədvəlində "pending" xanalarını doldur.
