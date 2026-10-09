# Gemini demo integration — bounded handoff

**READY — bu engineering goal üçün.** Bir fresh Gemini region visual observation + two-stage judgment existing CLI vasitəsilə alındı; Ali-nin evidence.json report ZIP-ə daxil edildi və actual browser download yoxlanıldı. Bu, useful QA accuracy və ya release-ready product claim-i deyil. Final policy **NEEDS_REVIEW**-dur.

## Git və scope

- Branch: `feat/hackathon-demo-integration`.
- Celal checkpoint: `7e7bb5da2984e82b5910685a11fb826e9bf82efb`; shared original base: `b7aa8b8a2155cdbe2f71f9598fd25c3f50ed5683`.
- Fetch edilmiş Ali branch exact SHA: `0b75b8acad7819483ce8e8c1c30b96c07515dd3c`.
- Required imports: `08a0c3f3efae6817019175e86ce247242ba280ff` → local `08f851a27f191ba463b3ad91130f27adfb2b7102`; `667925f2b77fe3e290234f4bf774bc895393dc32` → local `de3bcdee47f70bfbdd27f4509c8160bc6b954af9`.
- Ali A0 status və probe config remote commit-dən `git show` ilə oxundu; dev12 selection commit import edilmədi və batch işlənmədi.
- Smoke execution HEAD: `de3bcdee47f70bfbdd27f4509c8160bc6b954af9` + integration working diff. Delivery SHA final chat və ignored `final-git-state.json`-da qeyd edilir. Captured runtime identity execution checkpoint-i göstərir; delivery commit ilə qarışdırılmasın.
- Start: **15:26:49 Asia/Baku**. Cutoff: **15:45**; yeni inference smoke-dan sonra dayandırılıb. Master/main dəyişdirilməyib; mövcud work/caches/history qorunub.

## Environment, config və inputs

Existing `.venv`, CUDA Torch 2.6.0+cu124, OpenCV 4.12.0, cached frozen DINOv2 reuse edildi. Install/model download, billing enable və Ali host job yoxdur. `GEMINI_API_KEY` process-də əvvəl görünmürdü; Windows **User** environment-dən dəyəri göstərilmədən həmin variable-a yükləndi. Heç .env/key faylı yaradılmadı.

`configs/gemini_integration.yaml`: provider=openai, exact response model **gemini-3.5-flash**, endpoint `https://generativelanguage.googleapis.com/v1beta/openai/`, image_detail=null, reasoning_effort=low, timeout=60s, max_attempts=1, transient_retries=0. Ali successful probe model istifadə edildi; real response model field bunu təsdiqlədi. Proposal cap/default thresholds/crop sizes/prompt v9/policy dəyişməyib. Config hash **4f3bafbebc3b**. New cache `data/cache_gemini_integration_20261009`; artifacts `artifacts/gemini-integration-20261009`.

Ali bundle/inventory/human labels bu checkout-a supplied deyildi. Fallback **vr_562bb641**, restored real dev Youtube-Cutscene pair, 1207×718; independent human annotation **UNVERIFIED**. PNG-lərin SHA-ları mövcud provenance ilə yenidən match edildi:

- Reference: `86fa5576424d9c9cea29a0209ce79ed1deb0c1b47207fc9c6b88d9a22fa2803f`.
- Candidate: `9db614710c66a68f0df0cac705a7c9e6414c6725cb717243b0000485610ec0a4`.
- Dataset revision: `2afbfdcc9cb84318845f348c023bb2e92b942e29`. Label selection history provenance-dədir; inference requests yalnız images/observations və A1/D1 rules alıb, eval labels deyil.

## Fresh execution

Run **20261009T113207Z-ab2d55**: engine_mode real; CUDA float32 DINOv2; execution_status complete. Bu native flags scene judgment validation problem-ini gizlətmir.

**4/8 generation attempts**; 2 image stage-1 + 2 text stage-2, warmup=0, retries=0. Bütün calls HTTP 200 və captured network requests-dir. Əvvəl empty/absent cache namespace; provider capture fresh calls sübut edir. Export-un evidence cache field-i Ali schema üzrə `unknown (replay possible)` saxlanılır, çünki export per-call cache identity saxlamır. Freshness ayrıca `provider-calls.json` və runtime identity-dən məlumdur. Qalan 4 attempt **istifadə edilmir**; provider account quota remaining ölçülməyib.

CLI wall **55.4300s**, pipeline **47.7790s**, DINO features **1.6104s**. Call latencies: **4.3690 / 5.2224 / 4.8784 / 28.2683s**. Region validated=true, forbidden/D1, errors=[]; scene raw forbidden/D1 provider cavabı mövcud evidence guard tərəfindən uncertain, validated=false-a endirildi.

Final exact policy reason:

> Needs review: alignment unreliable or missing; proposals truncated (1/1 judged); R1: forbidden; SCENE: invalid or failed model response.

Alignment unreliable; proposal R1 `[0,0,1207,718]`, source dinov2, truncated=true. Scene error:

> audit forbidden claim has no pixel evidence outside proposed regions; downgraded to uncertain

Bu full-frame scene guard davranışı bu run-da **EXECUTED**-dir. Region JSON validation vizual həqiqəti və benchmark label correctness-i sübut etmir. Prompt/threshold/guard tuning edilmədi; adapter failure yoxdur, guard follow-up Ali/product roadmap-a qalır.

### Exact fresh provider outputs

**Region stage-1 observation**

```json
{
  "before_shows": "A bald security guard holding a gun to the head of a man (Michael) from behind, with Michael looking distressed and facing forward.",
  "after_shows": "The bald security guard holding a gun pointed forward, while Michael is standing on the right side of the frame, facing left towards the guard.",
  "observed_change": "The characters' positions and animations are completely different, with Michael no longer being held hostage from behind.",
  "change_type": "moved",
  "any_difference": true
}
```

**Region stage-2 rule judgment**

```json
{
  "verdict": "forbidden",
  "rule_ids": [
    "D1"
  ],
  "evidence": "The characters' positions and animations are completely different, representing a major scene composition change where Michael is no longer being held hostage from behind."
}
```

**Scene stage-1 observation**

```json
{
  "before_shows": "A bald security guard holding a gun to the head of a dark-haired man who is facing forward with a distressed expression.",
  "after_shows": "The same bald security guard holding a gun, but the dark-haired man is now in profile on the right side of the frame, facing left towards the guard.",
  "observed_change": "The camera angle and character positions/poses are completely different between the two shots.",
  "change_type": "moved",
  "any_difference": true,
  "other_changes_outside_boxes": true
}
```

**Scene stage-2 rule judgment**

```json
{
  "verdict": "forbidden",
  "rule_ids": [
    "D1"
  ],
  "evidence": "The camera angle and character positions/poses are completely different between the two shots, representing a major scene composition change."
}
```

## Checks və export

- `pytest -m 'not real_model' -q -ra -p no:cacheprovider --basetemp "$env:TEMP/gameqa-gemini-integration-pytest"`: **186 passed, 6 deselected, 0 skipped, 17.93s**, exit 0. Includes imported provider tests, evidence/hash/ZIP tests, storage and Streamlit AppTest. Tool output provenance; full pytest log persist edilməyib. Deselected real-model tests passing sayılmır; real Gemini smoke ayrıca yuxarıdadır.
- `storage.export_report`: Ali `write_evidence(result, run_dir)` zipping-dən əvvəl çağırılır; `render_report(result, run_dir)` stored hashes verir. Return contract report.md dəyişməyib. Existing strict xfail marker integration completed olduğuna görə çıxarıldı.
- ZIP açılır: `testzip() is None`, 26 entries. evidence.json schema_version=1, documented top-level fields, input/rules and region crop hashes match; validated forbidden region və final REVIEW match. No credential value / Authorization header found in ZIP.
- Includes evidence.json, analysis.json, report.md, rules.yaml, reference/candidate/aligned images, overlay, crops, diagnostics; əlavə exact provider requests/images/responses və config/source identity var. Requests headers saxlanmır, image base64 placeholders exact PNG files-ə işarə edir.
- Actual browser localhost:8523 saved run **REPLAY** ilə açıldı; boxes, crops, observed text, D1, validated=True və scene guard warning görüldü. Analyze basılmadı. Browser Export ZIP download `C:/Users/celal/Downloads/20261009T113207Z-ab2d55.zip` tamamlandı və açıldı; server ZIP ilə bütün member contents eynidir. Whole ZIP byte hashes timestamps səbəbilə fərqləndi; content equality verified.
- Plain menu Rerun: eyni run ID, analysis SHA unchanged, yalnız 1 run directory; yeni inference əlaməti yoxdur. Analyze-only engine entry point code inspection ilə də təsdiqləndi. Browser replay fresh UI inference kimi təqdim edilmir.

Local evidence root: `artifacts/gemini-integration-20261009/`. `zip-verification.json`, `ui-verification.json`, `capture/summary.json`, `ui-replay.jpg`; ZIP `runs/20261009T113207Z-ab2d55.zip`. Bunlar ignored local outputs-dur; git commit/push assets/keys/models/caches daşımır.

## Changed files və qalan limitations

Ali imports adapter (`vision/judge.py`), report.py, provider/evidence tests, gemini.yaml, scripts/list_models.py, scripts/ali_export_evidence.py, .env.example, DECISIONS D16, evidence_shape.md gətirir; həmin Ali-owned məntiq independently rewrite edilmədi.

Own minimal changes: storage.py export hook; test_report_evidence.py xfail removal; configs/gemini_integration.yaml isolated provider/run config; scripts/gemini_smoke_capture.py bounded observer (8 calls, quota/failure stop, no headers, key redaction); .gitignore yalnız yeni cache namespace üçün; bu handoff.

Remaining: independent human-verification və Ali supplied bundle inventory yoxdur; real output üçün accuracy/generalization claim yoxdur. Alignment/truncation və scene guard final automation coverage-ni məhdudlaşdırır. Native DINO weights_sha256 field custom TORCH_HOME üçün unknown qalır; actual weight hash runtime-identity-dədir. Hosted quota/account remaining məlum deyil. Uploaded Gemini UI analysis bu task-da yenidən icra edilməyib; CLI fresh, UI replay/export verified. Reference approval/history dəyişdirilməyib.

**Stop:** implement roadmap gözlənilir. Prompt/crops/policy tuning, full benchmark, training və yeni product direction başlamır.
