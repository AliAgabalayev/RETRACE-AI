# ALI_HANDOFF - Ali-nin bu gunku hissesi (2026-10-09)

Bu sened yalniz Ali-nin hissesini (A0-A1, evidence workflow, demo/pitch materialları) əhatə edir. Celal-in hissəsi (final scoring, slide assembly) burada yoxdur. Branch: `feat/hackathon-vision-evidence`. Hec bir remote push və ya merge edilməyib (mən git əmri işlətməmişəm, yalnız `git log` oxumuşam).

## 1. Nə hazırdır (commit-lərlə)

| Commit | Mənası |
|---|---|
| `08a0c3f` | Gemini provider (OpenAI-compatible), 429/503 backoff, `reasoning_effort` |
| `cf861f1` | A0: dev12 seçimi (seeded, inference-dən əvvəl), image inventory, labeling sheets |
| `667925f` | `evidence.json` sidecar (`gameqa.report.build_evidence` / `write_evidence`) və evidence ZIP exporter |
| `0b75b8a` | A0 status və runtime inventory (Qwen RAM blocker, Gemini probe) |
| `e844aab` | Ali-nin human label-ları dondurulub (`docs/ali/labels_ali.csv`) |
| `cac62c7` | A1 alətləri: VLM input dump (per-call cache provenance), A/B/C runner, scorer |
| `a502c2d` | A1 diagnostic sənədi, Qwen-vs-Gemini reproducer, qərar D17 |

Bu faylın özü və `docs/ali/DEMO_VIDEO_NOTES.md`, `docs/ali/PITCH_EVIDENCE.md` hələ commit olunmayıb (git-workflow-master vasitəsilə commit etmək lazımdır).

## 2. A1 nəticəsi (n = 12 dev, 5 bug / 7 clean - Ali-nin label-ları)

| Arm | PASS/FAIL/REVIEW | Bug false-PASS | Clean PASS |
|---|---|---|---|
| A pixel | 12/0/0 | 5/5 | 7/7 |
| B full-frame VLM | 8/0/4 | 5/5 | 3/7 |
| C hybrid | 0/0/12 | 0/5 | 0/7 |

Mənbə: `docs/ali/A1_diagnostic.md`, `docs/ali/a1_evidence/score_raw.md`. Bu, *development diagnostic*-dir, held-out deyil. Qərar D17 (`docs/DECISIONS.md`): Qwen build dondurulur, vision kodu dəyişmir. Səbəb: Unity bug-larda lokalizasiya düzgündür (DINOv2 proposal-ları Ali-nin box-ları ilə uyğun), problem VLM perception-dadır (Gemini 2/2 düzgün təsvir etdi, Qwen 0/2).

## 3. Nə qismən / ölçülməyib
- Observation accuracy (hədəf 10/12) **ölçülməyib**: `docs/ali/a1_evidence/obs_review.csv` doldurulmayıb. Rəqəm iddia etməyin.
- Label-ların 5 sətri Claude təklifi + Ali təsdiqi idi, və label-lar ilk model output-dan (15:21) sonra 15:38-də donduruldu (`label_provenance` sütunu). Bu zəiflik pitch-də qeyd olunmalıdır.
- `evidence.json` normal UI/CLI export-da yazılmır: `report.write_evidence` hələ `pipeline.py`/`storage.py`-dən çağırılmır (grep ilə yoxlandı: yalnız `report.py`-də tərif). Müvəqqəti körpü: `scripts/ali_export_evidence.py`. Hook Celal-in işidir (`docs/ali/evidence_shape.md`, "Required additive hook"). Bu hook gələndə `test_plain_export_report_writes_evidence` strict xfail XPASS olub fail verəcək - marker-i silin. Mən bu script-i işlətməmişəm; real ZIP-i açıb yoxlamaq lazımdır.
- Cache status hesabatda "unknown (replay possible)" göstərilir (per-stage provenance yoxdur). A1 run-ları təzə namespace-də (`data/cache_ali_a1`) olub, `calls.jsonl`-da per-call provenance var.
- Gemini yalnız 2 çağırış ilə sınanıb (free tier 20 sorğu/gün/model, D16).
- Dev12 cütləri `split: dev`-dir, UI-nin "Demo pair" siyahısında görünmürlər; upload ilə və ya saxlanmış run-ı yükləməklə göstərin.

## 4. A1-i necə təkrar etmək olar
Şərtlər: `.venv`, Ollama işləyir və `qwen2.5vl:3b` yüklənib, `data/work/<id>/` şəkilləri mövcuddur. İnferensdə label-lar istifadə olunmur.
```
cd /home/aliagabalayev/Desktop/Workspace/neuroscience-hackhaton
.venv/bin/python scripts/ali_a1_run.py --config configs/ali_a1_qwen.yaml --ids dev12 --arms A,B,C
.venv/bin/python scripts/ali_a1_score.py
```
Run resumable-dir (eyni əmri yenidən işlət). Real run `artifacts/ali/vlm.lock` tutur. Təxmini vaxt: B 38-48 s/cütlük, C 69-160 s/cütlük (CPU). Təkrar run-da cache namespace-i təzə seçin, əks halda nəticələr cache-dən gələr. Bu tam təkrarı mən bu sessiyada işlətməmişəm; sənəd A1 run-larının qeydlərinə əsaslanır.

Qwen-vs-Gemini reproducer: `docs/ali/a1_evidence/stage1_qwen_vs_gemini.json` + iki giriş PNG-si. Təkrar üçün `GEMINI_API_KEY` mühit dəyişəni lazımdır (açarı heç yerə yazmayın) və kvota məhduddur.

## 5. Evidence harada
- Raw predictions: `docs/ali/a1_evidence/predictions_{A,B,C}.jsonl`, scorer çıxışı `score_raw.md`, `obs_review.csv`.
- VLM-in gördüyü şəkillər: `docs/ali/a1_evidence/vr_4b921c5d_R1_vlm_input.png`, `vr_d07179d5_R1_vlm_input.png`; hamısı `artifacts/ali/a1_inputs/a1/<arm>/<id>/` (ignored/lokal ola bilər).
- Labels: `docs/ali/labels_ali.csv`; contact sheet-lər `docs/ali/contact_sheet_*.png`.
- Saxlanmış C run-ları: `artifacts/20261009T112802Z-c4530d` (vr_4b921c5d), `20261009T112407Z-355ff0` (vr_330651ed), `20261009T113543Z-8a257e` (vr_09a066d3).
- Decision qeydləri: `docs/DECISIONS.md` D16-D17. Evidence formatı: `docs/ali/evidence_shape.md`.
- Pitch və video: `docs/ali/PITCH_EVIDENCE.md`, `docs/ali/DEMO_VIDEO_NOTES.md`.
- Untracked qalan: `data/cache_ali_a1/`, `data/cache_ali_fresh/` (cache, commit etməyin).

## 6. A3-A5 üçün açıq işlər
**A3 (frozen comparison, 16:50-17:30):**
- Celal ilə razılaşdırılmış dondurulmuş build/config-i (`configs/ali_a1_qwen.yaml`) işlət; B və C eyni model/rules/aligned input istifadə etməlidir; error, dublikat, çatışmayan ID-ləri yoxla; REVIEW hallarını silmə.
- Dev12 hələ də development diagnostic-dir; held-out kimi təqdim etmə.
- Ən azı bir real failure nümunəsini saxla: vr_4b921c5d (artıq `PITCH_EVIDENCE.md`-də).
- Hybrid faydalı qərarları yaxşılaşdırmırsa, sadə metodu dəstəklə; DINOv2 üstünlüyü iddiası yoxdur.

**A4 (demo/video, 17:30-18:45):**
- `DEMO_VIDEO_NOTES.md` shot list-i ilə qeyd et; replay seqmentləri `REPLAY` ilə işarələ; live wall time-ı ayrıca ölç.
- Yazmazdan əvvəl ZIP-də `evidence.json` olduğunu real açıb yoxla.
- Qadağan: "fine-tuned", "production-ready", "reduces QA workload"; vr_4b921c5d üçün "FAIL".

**A5 (acceptance, 18:45-19:30):**
- Başqa cihazdan yoxla; yalnız replay/video varsa, həmin imkanı dəqiq adlandır.
- ZIP-i aç; Celal-in pitch rəqəmlərini raw sətirlər və denominator-larla (5/7, n=12) tutuşdur.
- Paket: code commit, launch əmri (`.venv/bin/streamlit run app.py`), model/config identity, input provenance, raw predictions, metrics, report ZIP, video, pitch, limitations.
- Submit edən insan 19:30-a qədər təsdiqi saxlayır. Mən heç bir xarici mesaj göndərməmişəm.

## 7. Aydın olmayanlar (unknown)
- Live wall time: ölçülməyib. UI-nin dev12 cütləri üçün `configs/ali_a1_qwen.yaml`-ı necə götürdüyü yoxlanmayıb. Rules-i UI formasında yükləmə addımları yoxlanmayıb. `scripts/ali_export_evidence.py` və `streamlit run app.py` bu sessiyada işlədilməyib.
