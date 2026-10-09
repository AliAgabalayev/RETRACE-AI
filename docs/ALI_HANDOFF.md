# Ali handoff — final evidence və təqdimat

9 oktyabr 2026, Bakı, ~18:02 checkpoint. Submission **19:30**, rəsmi deadline **20:00**. Implementation freeze qüvvədədir; presentation, docs, verification və submission qalır.

**Hazır:** end-to-end prototype, Qwen baseline, C2 raw cross-check, C4 UI-ready repo checkpoint, test evidence, pitch/video script, 7-slide PDF/PPTX və 110 s motion draft. **Final acceptance açıqdır:** Ali local C4 pre-flight, actual C2 ZIP bundle/full captures, final UI recording, second-device check və human submission confirmation.

**Repository consolidation:** latest fetched integration delivery **`68501897746bf674d582fd810cd9d7e2cfb943e6`**, runnable C4 UI code **`be1ea0acce271df994b516f6fa297118e981a3dd`**. [Runbook](FINAL_DEMO_RUNBOOK.md) və [verification](C4_DEMO_VERIFICATION.json) Celal host-da replay/browser export readiness göstərir; fresh C4 inference yoxdur. Independent offline C4 suite **197 passed, 6 skipped, 8.79 s**. Model/policy/config unchanged-dir. Ali final docs latest integration-a reconcile olunur; sonra reviewed PR ilə `master`-ə toplamaq Ali tərəfindən istənilib. [Git finalization](ali/GIT_FINALIZATION.md). Remote merge/submission hələ edilməyib.

**17:46 əlavə local UI baxışı:** main checkout integration79a0ef7-dir; OpenRouter config ilə http://localhost:8501, health200/AppTest0exceptions. Ali `.env` update ilə initial auth401-i həll etdi: auth200, fresh app process dotenv key istifadə edir; generation edilməyib. [UI_LOCAL_OPENROUTER.md](ali/UI_LOCAL_OPENROUTER.md). Final recording gate ayrıca saxlanılır. Main checkout switch-dən sonra deck/PNG copies `artifacts/ali/presentation/`-dadır; tracked docs ayrıca docs branch-də qalır.

## Source və runtime identity

| Identity | Dəyər |
|---|---|
| Confirmed integration branch | `feat/hackathon-demo-integration` |
| C2 raw verification source SHA | `79a0ef740196cbaa0639579386c6c591d2bfd8ca` |
| Latest fetched integration delivery SHA | `68501897746bf674d582fd810cd9d7e2cfb943e6` — Ali active UI still79a0ef7 |
| Freeze implementation code SHA | `bdd93fb534e8c0e9b574e60d383bc8b14dd03bf3` |
| Historical C2 inference code SHA | `c917532ac3161a0886f626985c53307eb2d477d8` — raw identity dəyişdirilməyib |
| Runtime | OpenRouter / `google/gemini-3.5-flash` / low / prompt v9 |
| Canonical config | `configs/openrouter_gemini_pilot.yaml`, merged hash **`eaa371255716`** |
| B diagnostic config hash | `2dfeb64cd673` — output/cache namespace paths fərqli |
| Ali vision freeze | `3591f7b`; fetched `74f84cf` əvvəlki integration merge-dir |
| Report scope fix | `3b794aa` PR #3 history-dədir və final source-da saxlanılıb |
| C4 UI-ready code SHA | `be1ea0acce271df994b516f6fa297118e981a3dd`; delivery6850189. Celal replay/browser checks READY; Ali local pre-flight pending |

Git-workflow-master exact delivery SHA-nı fetch ilə təsdiqləyib. `3591f7b` ancestor-dur; vision/report source frozen checkpoint ilə byte-for-byte eynidir. Detached verification checkout `/tmp/ali-c2-79a0ef7.ROajGB/checkout`-dur. Presentation/docs local hazırlanır; push/PR agent tərəfindən edilmir.

## C2 — final development runtime evidence

Independent recompute: [C2_VERIFICATION.md](ali/C2_VERIFICATION.md), [C2_RECOMPUTED.json](ali/C2_RECOMPUTED.json). Mənbə exact `79a0ef7`-də `docs/c2_openrouter/` raw predictions, calls, stages, identities, usage və ZIP verification records-dur. 12 unique dev pair, 5 bug/7 clean; missing/duplicate IDs yoxdur.

| Arm | PASS /FAIL /REVIEW | Coverage | Bug false-PASS | Bug FAIL | Clean PASS | Clean false-FAIL |
|---|---|---|---|---|---|---|
| C2 B full-frame VLM |1 /4 /7|5/12 (41.7%)|1/5|2/5|0/7|2/7|
| C2 C hybrid |1 /4 /7|5/12 (41.7%)|1/5|3/5|0/7|1/7|

**4 FAIL = 4 düzgün bug detection deyil.** C-də 3 bug FAIL və 1 clean false-FAIL var. B/C aggregate sayları eynidir, 10/12 pair eyni qərardır; booth C FAIL/B REVIEW, `vr_ef9b073a` C REVIEW/B FAIL. DINOv2 advantage ayrıca ablation ilə göstərilməyib.

- **Missing pedestal `vr_c1f47c57`: hər iki arm yanlış PASS verir.** D1 label qalır; post-freeze audit small table object təsvirini missing stone pedestal kimi düzəldib. Bu main failure video/pitch-də saxlanılır.
- Genuine clean PASS yoxdur: **0/7** hər iki arm-da. Outfit `vr_09a066d3` REVIEW-dur.
- 80 fresh call/stage records, 0 application cache hits, 0 retries, HTTP200 80/80. **B+C provider-reported total $0.2871945**; C $0.1934625/56 calls, B $0.0937320/24 calls. Invoice independently verified deyil.
- Celal host-da median orchestration wall C39.99005 s, B19.7196 s. Bunlar UI timing deyil; Ali Qwen host-u ilə hardware-controlled speed comparison sayılmır.
- Raw-level config/model/prompt/usage checks verified-dir. Exact inventory rules və labels-in inference-dən uzaq tutulması Celalın execution report/implementation provenance-ına əsaslanır; full request/image capture audit bundle gələndə tamamlanır.

## Qwen A1/A3 — baseline comparison

Qwen 2.5-VL3B, prompt v9; A1 hash `3a144cfcbb67`, A3 `642b6e26f39d` (dump/cache namespace fərqi).

| Arm | PASS /FAIL /REVIEW | Coverage | Bug false-PASS | Clean PASS |
|---|---|---|---|---|
| A pixel |12 /0 /0|12/12|5/5|7/7|
| B full-frame |8 /0 /4|8/12|5/5|3/7|
| C hybrid |0 /0 /12|0/12|0/5|0/7|

C bütün pair-lərdə abstain edir; 9/12 global-change collapse-dir. A3 A1-i 36/36 semantic row-da təkrarlayıb, 80 fresh calls; **determinism check**, yeni sample deyil. Observation marks B y+p4/12, C9/12; strict y1/12 hər ikisi. Bir rater, partial credit və possible anchoring caveat saxlanılır.

**Label limitations:** labels A1 başladıqdan sonra dondurulub; 4/5 bug label assistant təklifi/düzəlişi + Ali təsdiqindən gəlib. Dev12 mixed-source development diagnostic-dir, held-out deyil; Unity samples hamısı bug-dur. `vr_330651ed` subtitle language change üçün cutscene rules-da text rule yoxdur: ambiguous kimi açıqlanır, frozen D1 dəyişdirilmir. Sensitivity-only Qwen A/B false-PASS4/4, C0/4 at coverage0/12. Historical eval60 başqa build-in regression nəticəsidir.

## Demo run-ları və recording gate

| Shot | Runtime / run ID | Nəticə |
|---|---|---|
| C2 barrel | `20261009T123704Z-8e4e19` | FAIL R1(D1), SCENE(D1); 4 fresh calls; orchestration wall31.520s, pipeline30.2167s |
| C2 pedestal | `20261009T124621Z-0b0c2b` | **False-PASS**, missing pedestal |
| C2 outfit | `20261009T123947Z-584a66` | REVIEW; clean PASS deyil |
| Qwen barrel baseline | `20261009T112802Z-c4530d` | REVIEW; model texture/lighting deyir |
| C1 fallback barrel | `20261009T115633Z-83936b`, direct Gemini hash `6cfbba559386` | FAIL R1(D1); CLI25.4442s, pipeline18.4305s; Celalın prior UI replay/download check-i |

**Final recording C4 UI-ready integration UI-da edilir; Qwen branch UI istifadə edilmir.** [C4 runbook](FINAL_DEMO_RUNBOOK.md) exact Windows launch command, run IDs və browser replay/download evidence-i ehtiva edir. Celal host-da barrel və subtitle browser ZIP source ilə byte-identical yoxlanıb; C4 calls0, fresh UI inference yoxdur. Ali local C4 launch və bundle/export pre-flight hələ pending-dir. Deployment URL hazırda məlum deyil.

Linux canonical launch form (local self-test bu config ilə açıldı; final recording hələ pending-dir):

```bash
GAMEQA_CONFIG=configs/openrouter_gemini_pilot.yaml .venv/bin/streamlit run app.py
```

Credential adı `OPENROUTER_API_KEY`-dir; dəyər source/report/log-a yazılmır. Hər real VLM job `artifacts/ali/vlm.lock` tutmalıdır. Bu continuation-da **heç bir VLM job işlədilməyib**. Final footage saved runs-dan hazırlanacaq; açıq REPLAY label tələb olunur.

## Presentation və motion artifact-ləri

- [Pitch PDF](ali/pitch/AI_Gaming_Pitch.pdf), [PowerPoint](ali/pitch/AI_Gaming_Pitch.pptx): 7 səhifə; problem → pipeline → barrel success → measured comparison → pedestal failure → evidence ZIP → next pilot.
- [SLIDE_HANDOFF.md](ali/SLIDE_HANDOFF.md): 7×1920×1080 PNG və Celal üçün ayrıca 3 science PNG; tələb olunan UI kadrları.
- [PITCH_EVIDENCE.md](ali/PITCH_EVIDENCE.md): verified numbers, source identities və limitations.
- [DEMO_VIDEO_NOTES.md](ali/DEMO_VIDEO_NOTES.md): **113 s** labelled final recording shot list; actual final video hələ yoxdur.
- [MOTION_HANDOFF.md](ali/MOTION_HANDOFF.md): [110 s silent motion evidence draft](../artifacts/ali/motion/ali_evidence_motion_DRAFT_110s.mp4), 1920×1080, H264/30fps, 5,700,613 bytes. FFprobe/full decode PASS; 7/7 source hashes final PNG-lərlə match.
- Motion SHA256 `cda409954b356249d71c37d92cc4fdf9a0a7c39f8228fb19a9db6b9033dee228`. Video boyunca PRERECORDED / DRAFT / UI RECORDING PENDING labels var. Narration guide ayrıca artifact-dir; voice-over yoxdur.
- **Final video path, team acceptance və submission confirmation: PENDING.** Motion draft final UI recording və submission-ready narrated demo deyil.

PPTX səhifələri image-based-dir. PDF7pages, PPTX CRC/XML7slides və representative PNG readability yoxlanıb; desktop slide reader və second-device review gözlənir. Renderers local artifacts-dən istifadə edir, inference çağırmır.

## Verification və açıq acceptance

Latest C4 source `6850189`-də independent offline pytest **197 passed, 6 skipped, 8.79s**. C2 verification source `79a0ef7`-də əvvəlki suite **194 passed, 6 skipped, 5.14s**-dır. Real-model skips passing sayılmır. Əvvəlki docs branch193/6 və Celal C2 suite186/6deselected ayrı nəticələrdir.

Manifest hashes dəyişməyib: inference `245815f5191e6708`, labels `a10ab8dd2f936ada`, eval60 IDs `ff765d14428cd944`. `prepare_data.py` işlədilməyib. 3 local Qwen demo ZIP CRC/required members/6hashes-each check keçib; global-change collapse wording həmin local exports-da mövcuddur.

12 C2 ZIP üçün committed verification records raw run IDs/decisions ilə match-dir. **Actual C2 ZIP bytes local checkout-da yoxdur**; CRC/member hash audit transfer-dən sonra edilir. Celal host-dakı `artifacts/c2-openrouter-20261009/` bundle-i gələndə existing Qwen artifacts üstünə yazılmır. Native cache status unknown (replay possible)-dır; fresh-call evidence ayrı records-dadır.

Qalan qəbul:

1. C4 UI-ready/launch/browser evidence repo-dadır; Ali host-da fresh C4 launch + saved-run pre-flight hələ pending-dir.
2. Actual C2 bundle: barrel/pedestal ZIP CRC, required files/stored hashes, full request input-label audit.
3. Ali final UI recording + narration, ≤120s; replay/live labels və timing ayrılığı.
4. Second-device check, final deck human review və package link-ləri.
5. Final handoff metadata19:25; authorized human submission **19:30** və confirmation.

Yeni features/model experiments/threshold tuning yoxdur. Pitch konkret observed behavior, rule, evidence və traceability üzərində qurulur; fine-tuned/production-ready/QA workload reduction/generalization claims istifadə edilmir.
