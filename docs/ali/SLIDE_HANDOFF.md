# Pitch deck və vizuallar — Ali → Celal

**C5 consolidation update:** final docs fetched integration487f202 üzərinə reconcile edilib; offline199passed6skipped. Compact barrel replay/captures `deploy/replay/barrel/`-də local/tracked-dir; all12C2ZIP və Ali freshUIcheck pending-dir. Deck source79/C4readiness685historicaldır, metrics unchanged-dir. Yeni render edilməyib. [Current Git plan](GIT_FINALIZATION.md).

9 oktyabr 2026, Bakı. Evidence source **`79a0ef740196cbaa0639579386c6c591d2bfd8ca`**; canonical C config **`eaa371255716`**. C2 raw rows/calls/usage lokal olaraq yenidən hesablanıb: [C2_VERIFICATION.md](C2_VERIFICATION.md), [C2_RECOMPUTED.json](C2_RECOMPUTED.json). UI-ready SHA ayrıca gözlənir; bu deck final UI recording deyil.

**C4 update:** UI-ready code `be1ea0acce271df994b516f6fa297118e981a3dd`, delivery `68501897746bf674d582fd810cd9d7e2cfb943e6` artıq repo-da təsdiqlənib: [runbook](../FINAL_DEMO_RUNBOOK.md). Celal replay/browser checks READY, no fresh C4 inference; Ali local launch/bundle pre-flight və final recording pending-dir. Yuxarıdakı waiting status historical-dır. Deck-in C2 evidence source/metrics dəyişmir; bu task-da render edilməyib.

## Hazır artifact-lər

- [7-slide PDF](pitch/AI_Gaming_Pitch.pdf)
- [7-slide PowerPoint](pitch/AI_Gaming_Pitch.pptx)
- [Slide PNG-lər](pitch/): `01_problem`, `02_flow`, `03_barrel`, `04_results`, `05_failure`, `06_evidence`, `07_next`; hamısı **1920×1080 / 16:9**.
- Celalın əvvəlki 3-image tələbi: [comparison](slides/01_comparison.png), [Qwen/Gemini same-crop reproducer](slides/02_perception.png), [pedestal failure](slides/03_pedestal_failure.png).

PDF 7 page olaraq açılır. PowerPoint package CRC və XML parse yoxlaması keçib; desktop PowerPoint/Google Slides reader-də ayrıca açılış hələ yoxlanmayıb. PPTX səhifələri rendered image-dir: text editor ilə ayrıca editable deyil. Celal PNG-ləri öz final slide template-inə də yerləşdirə bilər; mətn dəyişməsi üçün renderer mənbəsi mövcuddur.

## Təqdimatın hekayəsi

1. Screenshot fərqi qərar üçün yetərli deyil: QA dəyişiklik, applicable rule və evidence istəyir.
2. Frozen DINOv2 + pixel diff region tapır; VLM əvvəl təsvir edir, sonra rules ilə hökm verir; kod final qərarı çıxarır.
3. Barrel C2 run `20261009T123704Z-8e4e19`: FAIL / R1 / D1. Eyni pair Qwen-də REVIEW-dur. Slide actual model-input crop göstərir, UI screenshot deyil.
4. Qwen baseline və final C2 nəticələri, coverage və false-PASS birlikdə.
5. Missing pedestal C2 run `20261009T124621Z-0b0c2b`: yanlış PASS. Bu, allowed-change uğuru deyil.
6. ZIP schema, stored hashes, scope və explicit reference approval/history.
7. Pilot xərci, məhdudiyyətlər və fresh pre-labelled validation.

**C2 B/C sayları eyni olsa da bütün qərarlar eyni deyil:** 10/12 pair eynidir; booth C FAIL/B REVIEW, `vr_ef9b073a` C REVIEW/B FAIL. Hybrid-də 4 FAIL = **3 bug FAIL + 1 clean false-FAIL**. Full-frame-də 4 FAIL = **2 bug FAIL + 2 clean false-FAIL**. Hər ikisində bug false-PASS **1/5**, coverage **5/12**, clean PASS **0/7**. “4 bug tapıldı” deməyin.

**$0.2871945 B+C toplamıdır:** 80 fresh calls, eyni 12 pair iki arm-da. C ayrıca $0.1934625 /56 calls, B $0.0937320 /24 calls. Provider-reported cost-dur, invoice yoxlanmayıb.

Dev12 development diagnostic-dir, held-out deyil. Labels A1 başlayandan sonra dondurulub; 4/5 bug label assistant təklifi/düzəlişi + Ali təsdiqindən gəlib. DINOv2 advantage, generalization və QA workload reduction iddiası yoxdur.

## Recording üçün Ali-dən lazım olan kadrlar

Celal **UI-ready SHA** göndərəndən sonra həmin integration UI-da çəkilir:

- İki screenshot + exact allow/deny rules görünən input ekranı.
- Barrel saved run: FAIL banner, R1 crop, D1 rule və reason.
- Qwen REVIEW baseline: əvvəlki saved evidence ayrıca `REPLAY / Qwen baseline` label ilə; final app Qwen branch-dən başladılmır.
- Pedestal saved run: PASS banner + before/after missing pedestal; `FALSE-PASS / known failure` label.
- Outfit `vr_09a066d3`: REVIEW; genuine clean PASS kimi göstərilmir.
- Export ZIP click; endirilmiş archive-də `evidence.json`, `analysis.json`, `report.md`, `rules.yaml`, images və crops.

Hər saved run `REPLAY`, static artifact `PRERECORDED` label daşıyır. Live müddət video uzunluğundan çıxarılmır. Ətraflı 113 s shot list: [DEMO_VIDEO_NOTES.md](DEMO_VIDEO_NOTES.md). Motion evidence draft ayrıca [MOTION_HANDOFF.md](MOTION_HANDOFF.md)-dədir; narration və real UI recording gözlənir.

## Renderer

```bash
MPLCONFIGDIR=/tmp/ali-pitch-matplotlib .venv/bin/python scripts/ali_prepare_pitch.py
```

Renderer local frozen evidence-dən oxuyur və presentation artifact-ləri yaradır; provider call etmir. Final video ≤120 s, slides/video 18:45, acceptance 19:15, submission **19:30**. PDF/PPTX-dəki source identity delivery docs commit SHA ilə qarışdırılmır.
