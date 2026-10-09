# Motion video — presentation draft

Bu artifact product implementation və ya yeni model experiment deyil. Mövcud pitch PNG-lərindən **110 saniyəlik, 1920×1080, H.264, silent evidence walkthrough** hazırlanır. Final UI footage Celalın ayrıca UI-ready SHA-sı gələndən sonra çəkilməlidir. `79a0ef740196cbaa0639579386c6c591d2bfd8ca` implementation freeze identity-dir; UI-ready acceptance demək deyil.

**C4 update:** UI-ready code `be1ea0acce271df994b516f6fa297118e981a3dd`, delivery `68501897746bf674d582fd810cd9d7e2cfb943e6` [repo runbook](../FINAL_DEMO_RUNBOOK.md)-da READY-dir. Əvvəlki UI-ready waiting qeydləri historical-dır; Ali local C4 launch/bundle pre-flight, final UI footage və voice-over hələ pending-dir. Mövcud silent motion draft dəyişdirilməyib və bu repository cleanup task-da render edilməyib.

Video boyunca `PRERECORDED / EVIDENCE WALKTHROUGH` və `DRAFT / UI RECORDING PENDING` görünür. Evidence card-ları saved inference nəticələrini təqdim edir. Renderer nə Streamlit-i başladır, nə VLM-ə call edir; heç bir ekran live UI kimi qurulmur. PNG-lər tam saxlanaraq header/footer üçün ayrıca letterbox sahəsinə yerləşdirilir; screenshot və text zoom edilmir.

## Render

```bash
.venv/bin/python scripts/ali_render_motion.py
```

PNG düzəlişindən sonra yalnız dəyişmiş scenes-i yeniləmək üçün `.venv/bin/python scripts/ali_render_motion.py --reuse-unchanged` işlədilir. Asset SHA-256, source caption və timing uyğun gəlməyən segment yenidən encode edilir; concat/probe/preview/manifest hər dəfə yenilənir.

Inputs: `docs/ali/pitch/01_problem.png` … `07_next.png`. Output yalnız git-ignored `artifacts/ali/motion/` daxilindədir. Mövcud FFmpeg və FFprobe istifadə olunur; dependency install və network yoxdur. Əsas fayl `ali_evidence_motion_DRAFT_110s.mp4`; əlavə files `motion_manifest.json`, hər shot üçün `preview_*.png`, silent draft-a ayrıca voice-over yazmaq üçün `narration_guide_AZ.srt`-dir. SRT video daxilinə burn olunmur və audio yaradılmır.

| Vaxt | Visual | Source |
|---|---|---|
| 00:00–00:13 | Problem framing | PROJECT_BRIEF; measurement claim yoxdur |
| 00:13–00:29 | Frozen pipeline | final code `79a0ef7`; config `eaa371255716` |
| 00:29–00:46 | Missing barrel | `vr_4b921c5d`: C2 Gemini FAIL və A1 Qwen REVIEW |
| 00:46–01:08 | Results | 12 development pairs; raw C2 B/C rows |
| 01:08–01:28 | Missing pedestal failure | `vr_c1f47c57`: B/C false-PASS |
| 01:28–01:40 | Evidence ZIP / runtime | call/cost və Celalın ZIP verification records-u; C2 ZIP bytes transfer-i pending |
| 01:40–01:50 | Limits və next steps | development diagnostic; labels caveats |

C2 üçün B və C hər ikisi 1 PASS / 4 FAIL / 7 REVIEW, coverage 5/12 (41.7%), bug false-PASS 1/5-dir. Bunlar video boyunca bir-birindən ayrılmamalıdır. Eyni aggregate count-lar eyni səhvlər demək deyil: C-də 3 bug FAIL + 1 clean false-FAIL; B-də 2 bug FAIL + 2 clean false-FAIL. B/C bərabərliyi DINOv2-hybrid advantage sübut etmir. Qwen observation y+p göstəricisi Gemini nəticəsi deyil.

Runtime: OpenRouter / `google/gemini-3.5-flash` / `reasoning_effort=low` / prompt v9. Provider-reported C2 cost `$0.2871945` **B və C birlikdə** 80 fresh call / 0 retries üçündür, tək C arm, bütün layihə xərci və future cost estimate deyil. C2 inference tarixi ilə son implementation SHA-sı ayrı saxlanmalıdır; son SHA-da nəticələrin re-run edildiyi iddia edilmir.

Labels model outputs başlayandan sonra final edilib; 5 bug label-dan 4-ü Claude-proposed və Ali-confirmed-dir. `vr_330651ed` subtitle-only dəyişikliyinə görə ambiguous-dir. Dataset VideoGameQA-Bench, CC BY 4.0; attribution deck-də saxlanır.

## Verification və final video

Render tamamlandıqdan sonra script FFprobe ilə müddət, resolution, H.264 və audio yoxluğunu yoxlayır, source PNG və movie SHA-256-larını manifest-ə yazır. Hər shot-dan representative frame çıxarılır; readability ayrıca gözlə yoxlanmalıdır.

Final submission video üçün hələ tələb olunur: Celaldan UI-ready SHA; barrel və pedestal saved-run IDs; brauzerdən endirilmiş ZIP verification; human voice-over və playback review. Final UI çəkilişini Ali-nin Qwen branch UI-sından etmək olmaz. Bu draft hazır olduqda belə bu checklist tamamlanmış sayılmır. Live latency movie duration-dan çıxarılmır.

**Cari status (2026-10-09):** draft render tamamlanıb. Final movie `artifacts/ali/motion/ali_evidence_motion_DRAFT_110s.mp4`, **110.000 s / 1920×1080 / H.264 / 30 fps / silent**, **5,700,613 bytes**-dır. SHA-256: `cda409954b356249d71c37d92cc4fdf9a0a7c39f8228fb19a9db6b9033dee228`.

Həqiqətən yoxlanıb:

- `.venv/bin/python scripts/ali_render_motion.py --reuse-unchanged` — render + concat + FFprobe + 7 preview çıxarmaq uğurludur.
- `ffmpeg -hide_banner -v error -i artifacts/ali/motion/ali_evidence_motion_DRAFT_110s.mp4 -f null -` — bütün MP4 decode edilir, exit 0, error yoxdur.
- 7/7 source PNG hash-ləri final pitch assets-lə eynidir; 01 headline layout fix və 07 B+C cost-scope fix daxil edilib.
- 7/7 representative frame vizual yoxlanıb: text və source captions kəsilmir; draft/prerecorded ribbons content-i örtmür; progress strip görünür. Bu statik frame yoxlaması full human playback və audio review-un əvəzi deyil.

Video **presentation draft** olaraq təhvil verilir. Narration guide var, voice-over və final UI footage yoxdur. C2 ZIP bytes transfer-i və final browser download verification ayrıca pending-dir; source caption buna görə ZIP verification **records** deyir.
