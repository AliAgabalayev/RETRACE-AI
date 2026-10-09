# ALI_HANDOFF - Ali-nin bu gunku hissesi (2026-10-09, yenilənib A3-dən sonra)

Bu sened yalniz Ali-nin hissəsini (A0-A3, evidence workflow, demo/pitch materialları) əhatə edir. Celal-in hissəsi (final scoring, slide assembly) burada yoxdur. Branch: `feat/hackathon-vision-evidence`. Mən git əmri işlətməmişəm (yalnız read-only `git log` / `git branch -vv`).

Qısa nəticə: kod dondurulub (D17). Pipeline end-to-end işləyir və bütün 12 dev cütündə REVIEW verir. Bug-ların hamısını PASS edən sadə metodlar (A, B) təhlükəlidir; hybrid (C) təhlükəsizdir, amma coverage 0/12. A3 yenidən-run A1-i 36/36 sətirdə eyni təkrarladı: bu *replication*-dır, ikinci nümunə deyil.

## 1. Commit zənciri (read-only `git log`, vaxtlar Baku)

| Commit | Vaxt | Mənası |
|---|---|---|
| `08a0c3f` | - | Gemini provider (OpenAI-compatible), 429/503 backoff, `reasoning_effort` |
| `cf861f1` | 14:47 | A0: dev12 seçimi (seeded, inference-dən əvvəl), image inventory, labeling sheets |
| `667925f` | 14:48 | `evidence.json` sidecar (`gameqa.report.build_evidence` / `write_evidence`) və evidence ZIP exporter |
| `0b75b8a` | 14:53 | A0 status və runtime inventory (Qwen RAM blocker, Gemini probe). A1 run-ları bu kodla edilib |
| `e844aab` | 15:38 | Ali-nin human label-ları dondurulub (`docs/ali/labels_ali.csv`) |
| `cac62c7` | 15:39 | A1 alətləri: VLM input dump (per-call cache provenance), A/B/C runner, scorer |
| `a502c2d` | 15:48 | A1 diagnostic sənədi, Qwen-vs-Gemini reproducer, qərar D17 |
| `a5590a5` | 15:52 | Post-freeze label audit, demo video notes, pitch evidence, ilk Ali handoff. A3 run-ı bu kodla edilib |
| `04559f4` | 16:15 | A1 observation accuracy (Ali-nin marks), status board, A3 frozen config |
| `3b794aa` | 16:27 | Report scope "global-change collapse" adlandırır (QA-D6), label audit düzəlişləri (QA-D2..D4), QA pre-A3 acceptance, A3 evidence |

**Push vəziyyəti (`git branch -vv`):** local `3b794aa`, `origin/feat/hackathon-vision-evidence` ondan **1 commit geridədir** (`ahead 1`). Yəni `3b794aa` hələ push olunmayıb; push-u Ali əlləri ilə edir (agentlər push etmir). Bu fayl, `PITCH_EVIDENCE.md`, `DEMO_VIDEO_NOTES.md` və `docs/ali/A3_review.md`, `EXPERIMENT_REGISTRY.md`, `configs/ali_a3_qwen.yaml` kimi yeni fayllar `git status`-a görə untracked/dəyişilmiş ola bilər; onları commit etmək `git-workflow-master` ilə olur, sonra Ali push edir. Cache qovluqları (`data/cache_ali_a1`, `data/cache_ali_a3`, `data/cache_ali_fresh`) commit olunmur. Commit-lərin hamısı master-ə merge olunmayıb; PR draft qalır.

## 2. A1 / A3 nəticəsi (n = 12 dev, 5 bug / 7 clean - Ali-nin label-ları)

| Arm | PASS/FAIL/REVIEW | Coverage | Bug false-PASS | Clean PASS |
|---|---|---|---|---|
| A pixel | 12/0/0 | 12/12 | 5/5 | 7/7 |
| B full-frame VLM | 8/0/4 | 8/12 | 5/5 | 3/7 |
| C hybrid | 0/0/12 | 0/12 | 0/5 | 0/7 |

Mənbə: `docs/ali/A1_diagnostic.md`, `docs/ali/a1_evidence/score_raw.md`, A3 üçün `docs/ali/A3_review.md` (sec 3) və `artifacts/ali/a3/{A,B,C}/predictions.jsonl`. False-PASS həmişə coverage ilə birlikdə deyilir: C 0/5 at 0/12; A 5/5 at 12/12; B 5/5 at 8/12.

Həssaslıq (vr_330651ed clean sayılsa, 4 bug / 8 clean; `docs/ali/labels_audit.md`, `A3_review.md` sec 4): A 4/4 at 12/12; B 4/4 at 8/12 (clean PASS 4/8); C 0/4 at 0/12. Nəticə dəyişmir.

**A3 = A1 (determinizm / regression yoxlaması):** 36/36 sətir eyni decision, n_proposals, truncation cause, region box və verdict; stage-1 mətn 24/24 eyni; 80 təzə VLM çağırışı, 0 cache hit (`A3_review.md` sec 1-2; `docs/ali/EXPERIMENT_REGISTRY.md`). Yalnız vaxt sahələri fərqlənir. Bu, eyni host, temperature 0, n = 2 run üçün keçərlidir; ümumi determinizm zəmanəti deyil. Effektiv nümunə yenə 12 cütdür. A3-ü "ikinci eksperiment" kimi təqdim etməyin.

**Observation accuracy (yeni siqnal):** Ali-nin marks (`docs/ali/a1_evidence/obs_review.csv`, `A1_diagnostic.md`): B y+p 4/12, C y+p 9/12; strict y hər ikisi 1/12 (hədəf 10/12 ödənmir). Caveat-lar: bir rater (Ali), mümkün anchoring (marks söhbətdə göstərilən nümunə mətnə yaxındır), n = 12, partial credit subyektivdir; Claude bir sətirdə razılaşmır (vr_43773eb8 C: y), onda C 2 y / 7 p olardı. Əsas: bu yaxşılaşma düzgün qərarlara çevrilmədi (C-də 0 PASS, 0 FAIL). "DINOv2 daha dəqiqdir" demək olmaz; yalnız "region crop VLM-in təsvirini qismən düzgün etdi" demək olar.

Qərar D17 (`docs/DECISIONS.md`): Qwen build dondurulur, vision kodu dəyişmir. Səbəb: Unity bug-larda lokalizasiya düzgündür, problem VLM perception-dadır (Gemini 2/2 düzgün təsvir etdi, Qwen 0/2; n = 2 reproducer).

## 3. Diqqət: QA tapıntıları (`docs/ali/A5_acceptance.md`) və bunların səsdə/yazıda necə deyilməsi

| ID | Problem | Necə deməli |
|---|---|---|
| D1 | `vr_330651ed` cütünün cutscene `rules.yaml`-ında mətn qaydası yoxdur | "Rule D1 mətn dəyişikliyini qadağan edir" **demə**. De: subtitle dili dəyişib, qayda bunu aydın əhatə etmir, label qeyri-müəyyəndir, uncertainty yüksəkdir |
| D2 | 5 bug label-dan 4-ü (vr_4b921c5d, vr_d07179d5, vr_c1f47c57, vr_330651ed) model output-larından sonra Claude tərəfindən təklif/düzəliş olunub, Ali təsdiq edib | IoU 0.60 / 0.71 uyğunluğu tam müstəqil sübut deyil; "mənim müstəqil label-im" demə |
| D3 | `labels_audit.md`-də "10 pairs" səhv idi (9 ID) | düzəldilib |
| D4 | vr_d07179d5 label mətni "glass/texture" deyir, şəkil booth damı və TELEPHONE yazısının itdiyini göstərir | frozen label dəyişdirilmir; obs_review-da Gemini mətni doğrudur |
| D5 | vr_4b921c5d ZIP-də scene audit `allowed` deyir (yanlış) | Kamerada de: audit "allowed" dedi (səhv), region guard ziddiyyəti tutdu, yekun REVIEW-dur, FAIL deyil |
| D6 | Collapsed run-larda Scope bölməsi lokalizasiyanın çökdüyünü demirdi | `3b794aa`-da düzəldilib; demo ZIP-lər bundan sonra yenidən yaradılıb və "NOT assessed: global change ... collapsed" sətri var (mən `report.md`-ni grep etdim) |

## 4. Nə qismən / ölçülməyib
- `evidence.json` normal UI/CLI export-da yazılırmı: hook (`0e234d8`, Celal-in `feat/hackathon-demo-integration` branch-ı) bu branch-da deyil və mən yoxlamamışam. Hook gələndə `test_plain_export_report_writes_evidence` strict xfail XPASS olub fail verəcək; marker-i silin.
- Demo ZIP-lər `artifacts/ali/demo_zips/`-də mövcuddur (3 ədəd, hamısı NEEDS_REVIEW); QA onları açıb yoxlayıb (`A5_acceptance.md`, "Demo ZIPs"). Əvvəlki "export script işlədilməyib" qeydi köhnəlib. Kamera qarşısında göstərəcəyin ZIP-i yenə də `unzip -l` ilə yoxla.
- Cache status hesabatda "unknown (replay possible)" göstərilir (per-stage provenance yoxdur); A1/A3 run-ları təzə namespace-də olub, `calls.jsonl`-da per-call provenance var.
- QA-nın A3 vizual yoxlaması `docs/ali/A3_review.md`-yə əlavə olunur; bu faylı yazanda hələ oxuya bilmədim (unverified).
- Gemini yalnız 2 çağırış ilə sınanıb (free tier 20 sorğu/gün/model, D16).
- Live wall time ölçülməyib. CPU reference: B 37-49 s, C 63-161 s cütlük başına (`A3_review.md` sec 2).
- UI-nin dev12 cütləri üçün `configs/ali_a1_qwen.yaml`-ı necə götürdüyü, rules-i UI-ya yükləmə addımları və `streamlit run app.py` bu sessiyada yoxlanmayıb.
- Dev12 cütləri `split: dev`-dir, UI "Demo pair" siyahısında görünmürlər; upload ilə və ya saxlanmış run-ı yükləməklə göstərin.

## 5. A1/A3-ü necə təkrar etmək olar
Şərtlər: `.venv`, Ollama işləyir və `qwen2.5vl:3b` yüklənib, `data/work/<id>/` şəkilləri mövcuddur. İnferensdə label-lar istifadə olunmur.
```
cd /home/aliagabalayev/Desktop/Workspace/neuroscience-hackhaton
.venv/bin/python scripts/ali_a1_run.py --config configs/ali_a3_qwen.yaml --ids dev12 --arms A,B,C
.venv/bin/python scripts/ali_a1_score.py
```
(A3 run-ı bu config ilə edilib, `A3_review.md` sec 6. `scripts/ali_a1_score.py`-nin A3 üçün argumentlərini yoxlamamışam.) Run resumable-dır. Real run `artifacts/ali/vlm.lock` tutur; eyni anda başqa Ollama işi işlətməyin. Təkrar run-da təzə cache namespace seçin, əks halda nəticələr cache-dən gələr. Qwen-vs-Gemini: `docs/ali/a1_evidence/stage1_qwen_vs_gemini.json`; təkrar üçün `GEMINI_API_KEY` mühit dəyişəni (açarı heç yerə yazmayın), kvota məhduddur.

## 6. Evidence harada
- Raw: `docs/ali/a1_evidence/predictions_{A,B,C}.jsonl`, `score_raw.md`, `obs_review.csv`; A3 üçün `artifacts/ali/a3/` və `artifacts/ali/a1_inputs/a3/` (local, ignored ola bilər).
- Review/audit: `docs/ali/A1_diagnostic.md`, `A3_review.md`, `EXPERIMENT_REGISTRY.md`, `labels_audit.md`, `A5_acceptance.md`; status `docs/status/ali-today.md`.
- VLM-in gördüyü şəkillər: `docs/ali/a1_evidence/vr_4b921c5d_R1_vlm_input.png`, `vr_d07179d5_R1_vlm_input.png`.
- Saxlanmış C run-ları: `artifacts/20261009T112802Z-c4530d` (vr_4b921c5d), `20261009T112407Z-355ff0` (vr_330651ed), `20261009T113543Z-8a257e` (vr_09a066d3). Demo ZIP-lər: `artifacts/ali/demo_zips/`.
- Pitch və video: `docs/ali/PITCH_EVIDENCE.md`, `docs/ali/DEMO_VIDEO_NOTES.md`.

## 7. Qalan addımlar (vaxtlar `docs/status/ali-today.md`-dən; deadline 20:00, submit 19:30)
- **Hazırda (17:20-17:30):** docs commit (`git-workflow-master`), sonra Ali `3b794aa` və yeni commit-i əllə push edir, PR-ı ready edir (agentlər push etmir). 17:30-dan sonra yeni experiment, tuning, model run yoxdur.
- **A4, 17:30-18:45:** 15 - Ollama/Streamlit rehearsal (17:30); 16 - 90-120 s video `DEMO_VIDEO_NOTES.md` shot list ilə, seqmentlər `REPLAY` / `PRERECORDED` / `LIVE` ilə işarələnir (18:30-a qədər); 17 - live wall time ayrıca ölçülür, təzə boş cache, başqa yük yoxdur, n göstərilir (18:30-18:45); 18 - video + 3 slide şəkli (A1 cədvəli, Qwen vs Gemini, failure nümunəsi) Celal-a (18:45). Celal-dan 17:00-a qədər deployment URL varmı soruşulmalı idi; cavab `ali-today.md`-də yoxdur (unverified).
- **A5, 18:45-19:30:** qa-engineer başqa cihazdan yoxlayır (yalnız mövcud olanı; URL yoxdursa replay/video dəqiq adlandırılır), ZIP-i açır, Celal-in pitch rəqəmlərini raw sətirlərlə tutuşdurur (19:05), paket checklist (19:10): code commit, launch əmri (`.venv/bin/streamlit run app.py`), model/config identity, input provenance, raw predictions, metrics, report ZIP, video, pitch, limitations. Ali + Celal baxışı 19:20, submit 19:30; təsdiqi saxla. Mən heç bir xarici mesaj göndərməmişəm.
- Qadağan sözlər (iki sənəddə də): "fine-tuned", "production-ready", "reduces QA workload", DINOv2 üstünlüyü iddiası; vr_4b921c5d üçün "FAIL".
