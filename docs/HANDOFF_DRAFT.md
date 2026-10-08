# HANDOFF (qaralama) - documentation-engineer

Qeyd: bu qaralamadır; yekun `HANDOFF.md`-ni senior-pm yığır. "UNVERIFIED" = hələ heç bir status faylı və ya artifact bunun işlədiyini təsdiqləməyib. "BİLİNMİR" = kod/nəticə hələ yoxdur.

## 1. Nə işləyir, nə partial, nə incomplete-dir?
- Hazırdır (kod oxunub): `src/gameqa/contracts.py` (Pydantic contracts) və `src/gameqa/decision.py` (PASS/FAIL/NEEDS_REVIEW siyasəti). Bunların testləri hələ VERIFIED deyil.
- Kod oxunub (işlədilməyib, test nəticəsi yoxdur): `vision/alignment.py`, `vision/features.py`, `vision/proposals.py`, `vision/judge.py` + `prompts.py`, `pipeline.py`, `storage.py`, `report.py`, `imageio.py`, `rules.py`, `data/manifest.py`.
- Hələ yoxdur (yoxlanıldığı vaxt): `app.py`, `cli.py`, `scripts/evaluate.py`, heç bir `artifacts/<run_id>/` (yəni real DINOv2 + VLM run-ı sübut olunmayıb).
- Data: `docs/status/data-prep.md` ilkin 20 real pair hazır olduğunu yazır (tam 250 hələ gedir).
- QA: `tests/policy` üçün 46 pass, 3 xfail (QA status faylı). Bu, mənim işlətdiyim yoxlama deyil.

## 2. Setup/run üçün verified commands
- VERIFIED (status/senior-pm.md): `.venv` `--system-site-packages` ilə yaradılıb; `streamlit 1.65` quraşdırılıb; `pip install -e . --no-deps`; `ollama pull qwen2.5vl:3b` uğurlu.
- UNVERIFIED: `streamlit run app.py`, `python -m pytest`, CLI, data hazırlığı, evaluation.

## 3. Demo pair-lər və gözlənilən behavior
BİLİNMİR. `docs/DEMO_RUNBOOK.md`-ə bax (forbidden / allowed / uncertain-error placeholder-ləri). Synthetic fixture ilə real benchmark pair-i qarışdırma.

## 4. Screenshot-dan verdict-ə code path
`docs/CODE_WALKTHROUGH.md`. Qısa: `analyze()` -> `align()` -> `FeatureExtractor.distance_map()` -> `propose()` -> `Judge.judge_region()` + `Judge.audit_scene()` -> `decide()`. DINOv2 yalnız "harada fərq var" təklif edir, VLM "bu fərq icazəlidirmi" deyir, final qərarı isə kod (`decision.py`) verir. Hər mərhələ `docs/CODE_WALKTHROUGH.md`-də real fayl:sətir ilə izah olunub. Əsas fikir: pipeline heç vaxt xətanı PASS-a çevirmir - xəta, mock, uncertain, truncation, etibarsız alignment -> `NEEDS_REVIEW`; yalnız validasiya olunmuş real `forbidden` verdict `FAIL` verir.

## 5. Nəyi harada dəyişmək
- Threshold, region cap, timeout, model adı: `configs/default.yaml`.
- Qərar siyasəti: `src/gameqa/decision.py` (frozen; dəyişiklik senior-pm vasitəsilə, `docs/DECISIONS.md`-də qeyd).
- Prompt/VLM: `src/gameqa/vision/prompts.py` (dəyişəndə `PROMPT_VERSION` artır - cache key-in hissəsidir), response validasiya qaydaları `judge.py:validate_response`, mock davranışlar `MOCK_BEHAVIORS`.
- Rules: `configs/rules_example.yaml` (hələ yoxlanmayıb), benchmark üçün `data/manifest.py:rules_from_question`.

## 6. Hansı test/experiment həqiqətən işləyib?
Hələ heç biri status fayllarında qeyd olunmayıb. BİLİNMİR.

## 7. Ən vacib known failure
Hələ reproduce edilməyib. Qeydə alınmış məlum boşluqlar: QA-D3 (ziddiyyətli allow/deny rule-lar `decide`-də aşkarlanmır -> PASS ola bilər); `proposals.py` içində `_MAX_RAW=200` sakit kəsmə `truncated` qeyd etmir (kod oxunuşundan, ölçülməyib). Gözlənilən risklər (hələ ölçülməyib): kiçik obyektin yoxa çıxması 14 piksellik patch-də görünməyə bilər; alignment həssaslığı; `qwen2.5vl:3b`-nin JSON uyğunluğu və kalibrasiya olunmamış verdict-ləri; dataset-in selective download məhdudiyyəti.

## 8. Ali üçün növbəti üç iş (ilkin, phase 2-də dəqiqləşəcək)
1. `README.md`-dəki UNVERIFIED command-ları işə sal, nəticəni yaz.
2. Real DINOv2 + qwen2.5vl:3b ilə bir demo pair işlət, `artifacts/<run_id>/analysis.json`-u `docs/CODE_WALKTHROUGH.md` bölmə 5 ilə yoxla.
3. Dev split-də `dinov2_threshold` və `classical_threshold`-u ölç; small-object miss-i reproduce et.
