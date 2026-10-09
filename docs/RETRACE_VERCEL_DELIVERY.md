# RETRACE UI və Vercel delivery

9 October 2026, Asia/Baku. **BLOCKED — public deployment və original evidence download tamamlanmayıb.** UI/build success READY demək deyil.

## Actual state

İş qovluğu Windows handoff yolu əvəzinə `/home/aliagabalayev/Desktop/Workspace/neuroscience-hackhaton`-dur. Private GitHub giriş `AliAgabalayev` hesabı ilə verified-dir. Başlanğıc fresh master `7f93c0204b44f8e41cc5c1a688a135ea0f133e88`; iş zamanı sənədləşmə merge-i ilə son master `3d7dbf7db57e244846546cf99b360ae760710e2c` oldu. Feature `feat/retrace-vercel-ui` həmin son master üzərinə rebase edilir. User cache-ləri qorunur; repo private qalır.

Verified public URL: **yoxdur**. Deployed SHA: **yoxdur**. Vercel project/account/plan seçilməyib; preview və production yaradılmayıb. Bu sessiyada Vercel CLI/token/connected plugin yoxdur. Owner-dan Vercel bağlantısı və team seçimi istənilib. Portfolio dəyişdirilməyib; hosting plan/domain/storage alınmayıb.

## Implemented behavior

Native Streamlit dark theme: near-black, warm off-white, thin dividers, orange accent. Large RETRACE wordmark; screenshot comparison → final decision/observations → region crops/stored rules → evidence export → compact limitations. `celalibr.win` ayrıca browser profilində vizual yoxlanılıb.

`GAMEQA_PUBLIC_REPLAY=1` yalnız immutable `deploy/replay/barrel` package-i oxuyur; every manifest-listed file checksum yoxlanır. Default `20261009T123704Z-8e4e19`, sample `vr_4b921c5d`, original **FAIL**, label **“Recorded model run — replay, no new inference.”** Public rejim `.env` oxumur, engines/inference/uploads/mocks və reference approval açmır. Startup provider key-i child environment-dən çıxarır. Persistent history və evidence write yoxdur. Local analysis/approval safeguards qalır; existing Render-compatible Dockerfile dəyişmir.

OpenRouter / `google/gemini-3.5-flash` / low / prompt v9 / config `eaa371255716` unchanged. Source model/runtime identity və bütün **20** original package asset hash-ları unchanged. Missing pedestal false PASS limitation açıq göstərilir. Video/autonomous gameplay future features olaraq qalır.

## Original evidence blocker

Known original ZIP path `artifacts/c2-openrouter-20261009/runs-C/20261009T123704Z-8e4e19.zip` bu Ali checkout-da yoxdur. Portable package original inputs/crops/rules/analysis/captures/runtime identity saxlayır, amma original `report.md`, `evidence.json` və ZIP-i daxil etmir. Legacy local startup reconstructed export yaradır; bu original ZIP kimi təqdim edilmir və public startup bu yolu işləmir.

Expected original ZIP SHA256: `b739b23a055fd70937dcf741c9595acd2587d13b1ea289fbb56ea81539bd2554`. Original arxiv owner tərəfindən veriləndə secret scan və checksum yoxlamasından sonra **exact bytes** `deploy/replay/barrel.zip` kimi əlavə edilə bilər. Public UI yalnız həmin hash-ə uyğun archive-i və required analysis/evidence/report entries-i qəbul edir. Original report/evidence archive daxilində qorunmalıdır; regeneration və missing-asset fabrication yoxdur. Archive yoxdursa UI açıq error verir, download göstərmir.

## Native Vercel path — prepared, account-unverified

Current official [Container Images](https://vercel.com/docs/functions/container-images) sənədi `Dockerfile.vercel` auto-detection, OCI HTTP server, project setting ilə **PORT=8501**, stdout/stderr logs və Fluid Compute göstərir. Additive Dockerfile existing dependency/CPU DINO package-i saxlayır, public replay default-u əlavə edir. `.vercelignore` credentials, caches, local artifacts/history və unrelated docs/tests/data-ni upload-dan çıxarır. Runtime image yalnız explicit Docker COPY-ları daxil edir.

Official [WebSocket docs](https://vercel.com/kb/guide/do-vercel-serverless-functions-support-websocket-connections) native support-un public beta/all plans olduğunu bildirir. Connection bir instance-a pin olunur, max duration-da bağlanır; reconnect yeni instance-a düşə bilər. Immutable package hər instance-da olduğuna görə replay persistent storage istəmir. Actual Streamlit reconnect/media/download routing preview-də yoxlanmalıdır.

Official [Function limits](https://vercel.com/docs/functions/limitations): Hobby 2 GB/1 CPU və 300s; Pro/Enterprise max 4 GB/2 CPU və 800s, bəzi runtimes üçün extended 1800s beta. Bunlar account capability və measured RETRACE requirement deyil. Existing image-in historical 1.58 GiB ölçüsü yeni Vercel image ölçməsi deyil. [VCR limits](https://vercel.com/kb/guide/how-to-use-vercel-container-registry): compressed layer 500 MB, image 15 GB. Cold starts/hosted RAM ölçülməyib. Production idle scale-down 5min, preview 30s; SIGTERM 30s grace. Filesystem persistence gözlənilmir; public startup package-i read-only oxuyur.

ZIP/images üçün response-size gate də lazımdır: standard Function response limit 4.5 MB; [official guidance](https://vercel.com/kb/guide/how-to-bypass-vercel-body-size-limit-serverless-functions) streaming responses-in limitdən azad olduğunu deyir. Container/Streamlit media yolu ilə original full download-un işləməsi **unverified**-dir. External storage və rewrite başlanmayıb. Actual feature, filesystem və response behavior hesab/preview olmadan verified kimi təqdim edilmir.

## Actual verification

Local command (keyless, no new inference):

```sh
cd /home/aliagabalayev/Desktop/Workspace/neuroscience-hackhaton
env -u OPENROUTER_API_KEY GAMEQA_PUBLIC_REPLAY=1 PYTHONPATH=src PORT=8531 .venv/bin/python scripts/start_deployment.py
```

Local Python 3.13 / Streamlit 1.65 environment; Docker pins Python 3.12 / Streamlit 1.61.1. Local checks do not establish hosted/pinned-runtime success.

- `.venv/bin/python -m pytest -m 'not real_model' -q`: **208 passed, 6 deselected, 23.20s**. Real-model checks excluded; no new inference.
- Focused UI/deployment checks pass, including local safeguards, public immutable assets, no dotenv/engine/provider calls, absent/corrupt ZIP refusal, matching QA-only archive byte preservation and startup key stripping. QA archive simulations are not original model evidence.
- Real Brave browser via isolated `/tmp` profile/CDP: desktop 1440×1000, mobile 390×844, separate Streamlit session 1280×900; FAIL/replay label, originals/crops/observations/rules visible; desktop refresh passed; images decoded; horizontal overflow 0; console errors 0.
- Screenshots/results: `/tmp/retrace-browser-evidence/`; QA record `/tmp/retrace-qa-results.txt`. No key values in logs. Browser downloaded original ZIP/hash verification **not run: original archive unavailable**.
- Independent code review completed; startup flag whitespace defect found and fixed with parametrized regression.
- PR CI validates original Render Docker path and additive Vercel public image startup. Actual CI result is recorded in PR/final handoff, not inherited from older runs.
- Task provider API calls **0**, inference cost **$0**. Hosting cost not measured; no Vercel resources created.

## Remaining release gates and rollback

1. Owner connects Vercel account/team with current-plan container access and supplies original ZIP location. Do not put provider key in Vercel.
2. Verify original archive identity/asset hashes and secret scan; commit only exact relevant original evidence. Keep public Analyze/approval disabled.
3. Create a **new RETRACE** project, repo private, `Dockerfile.vercel`, `PORT=8501`, Fluid Compute; preview first. Preserve existing portfolio.
4. Browser verify Streamlit session/FAIL/rules/observations/original images/crops, complete ZIP containing evidence.json and manifest-matching assets, refresh, independent anonymous session, desktop/mobile, reconnect after max duration/cold start, no console error/secrets/API inference. Check normal HTTPS access without Vercel login wall.
5. Reviewed PR + all required checks green; merge normally, then deploy verified merged SHA to production and repeat unauthenticated URL/download verification. Record project, plan/settings, URL, deployed SHA and actual results here.
6. Rollback after a verified deployment: promote the previous verified deployment from Vercel project Deployments; if none exists, disable the new RETRACE deployment and fix on a branch. Source rollback through reviewed revert PR; no force push. No existing deployment was changed in this session.

If account features or actual Streamlit/large-download checks fail, stop and present the exact error. Smallest approved-scope alternative is an owner-authorized existing container host using the unchanged Dockerfile. It requires separate owner authorization; no host/storage purchase or framework rewrite is implied.
