# RETRACE UI və Vercel delivery

9 October 2026, Asia/Baku. **IN PROGRESS — public preview/production acceptance pending.** Build success READY demək deyil.

## Source və access

Ali iş qovluğu `/home/aliagabalayev/Desktop/Workspace/neuroscience-hackhaton`-dur. Private GitHub giriş `AliAgabalayev` hesabı ilə verified-dir. Başlanğıc master `7f93c0204b44f8e41cc5c1a688a135ea0f133e88`; feature `feat/retrace-vercel-ui` current master `3d7dbf7db57e244846546cf99b360ae760710e2c` üzərinə rebase edilib. [PR #9](https://github.com/AliAgabalayev/neuroscience-hackhaton/pull/9) draft-dır; initial head `a1214b645e6694d7bb0c1028095eba1997f86a6d` checks/container/GitGuardian SUCCESS. Latest export follow-up CI və reviewed merge pending-dir. User changes/cache-lər qorunub; repo private qalır.

Vercel CLI **63.1.0** login verified: `aliagabalazade00-2183`, team **octopus-e236** (Octopus), **Hobby**. New project **retrace-visual-qa**, ID `prj_2B36gpL9pecZOFDZADJ6bFtzQS0j`. Portfolio dəyişdirilməyib. Plan/domain/storage alınmayıb. Verified public URL və deployed SHA: **pending**.

## Implemented behavior

Native Streamlit dark theme: #090909 background, warm #F5F4F0 text, #303030 dividers, #E66B38 accent. Large RETRACE wordmark; comparison → final decision/observations → crops/stored rules → evidence export → compact limitations. `celalibr.win` isolated real browser-də vizual yoxlanılıb. Native controls və semantic CSS istifadə olunur.

`GAMEQA_PUBLIC_REPLAY=1` yalnız immutable `deploy/replay/barrel` package-i oxuyur və every manifest-listed checksum-u yoxlayır. Default run `20261009T123704Z-8e4e19`, sample `vr_4b921c5d`, recorded **FAIL**, label **“Recorded model run — replay, no new inference.”** Public rejim `.env` oxumur; engines/inference/uploads/mocks və persistent reference approval açmır. Startup provider key-i child environment-dən çıxarır. Runtime evidence/history yazılmır. Local analysis/approval safeguards və existing Render Dockerfile qalır.

OpenRouter / `google/gemini-3.5-flash` / low / prompt v9 / config hash `eaa371255716` unchanged. Original observations, runtime identity və bütün **20** original asset hash-ları unchanged. Missing pedestal false PASS limitation görünür. Video/autonomous gameplay future features-dir.

## Explicitly labelled portable evidence export

Original `artifacts/c2-openrouter-20261009/runs-C/20261009T123704Z-8e4e19.zip`, original report.md/evidence.json Ali checkout-da yoxdur. Relevant local paths, GitHub releases və Actions artifacts yoxlanıldı; archive tapılmadı. Historical ZIP SHA256: `b739b23a055fd70937dcf741c9595acd2587d13b1ea289fbb56ea81539bd2554`.

Owner **“Etiketli replay ZIP ilə davam et”** seçimini təsdiqlədi. `scripts/build_replay_export.py` offline stdlib builder bütün original bytes/package.json-u saxlayır; report.md, evidence.json və export-provenance.json açıq reconstruction metadata-sıdır. No model import, new inference və runtime regeneration yoxdur. `deploy/replay/barrel-replay.zip` **19,478,122 bytes**, SHA256 `7399de171e5c1514a057a466e4b3bc0535a24e2b2a56bee0a1d418a6c1942e9b`. Descriptor `deploy/replay/barrel-replay-export.json` archive və source identity-ni bağlayır.

UI caption: **“Portable replay export — original run files preserved; report and evidence index reconstructed. Original ZIP unavailable.”** Filename `20261009T123704Z-8e4e19-replay.zip`. UI archive checksum, all 20 source hashes, manifest bytes, identity/decision/provenance-ni doğrulayır. Original ZIP sonra exact bytes olaraq `deploy/replay/barrel.zip`-ə bərpa edilərsə native archive üstün tutulur; corrupt native archive fallback ilə gizlədilmir. Bu replay ZIP historical original ZIP kimi təqdim edilmir.

## Vercel configuration və constraints

Current official [Container Images](https://vercel.com/docs/functions/container-images) docs `Dockerfile.vercel` auto-detection və OCI HTTP server göstərir. Additive Dockerfile existing full CPU dependency/DINO cache path-ni saxlayır. Project **PORT=8501** və **GAMEQA_PUBLIC_REPLAY=1**, preview/production config variables. **OPENROUTER_API_KEY yoxdur.** `.vercelignore`/`.dockerignore` credentials, .vercel metadata, caches/artifacts-ni çıxarır; explicit COPY runtime assets. CLI link-in yaratdığı `.env.local` OIDC credential gitignored-dir, upload edilmir.

Actual first CLI deployment automatically targeted production despite no --prod; `dpl_AWdvALvnLo3BwkUxajDuQQhfsP1S`, source `ae47b252a4378f39af996c2e30deb59964492b12`. Build CLI62.7.0 reported ready in151ms without Docker build, but public `https://retrace-visual-qa.vercel.app` returned404 NOT_FOUND. It is **not a working release**. Explicit preview `dpl_BD6Cwb7CjvTztEeDfTb1CHUBfuoh` was **BLOCKED**, `TEAM_ACCESS_REQUIRED`: “The deployment was blocked because the commit author doesn’t have permission to create deployments for this project.” Owner was asked to connect GitHub AliAgabalayev in Vercel Login Connections; [official troubleshooting](https://vercel.com/docs/deployments/troubleshoot-project-collaboration) requires recognized Hobby team ownership. No authorship spoofing, plan upgrade or permission bypass.

To eliminate auto-detection ambiguity, `vercel.json` uses the official [Services](https://vercel.com/docs/services) single container runtime/entrypoint and catch-all rewrite. `/data` ignore is root-anchored so `src/gameqa/data` remains included. Actual service availability remains a verification gate.

CLI63.1 `vercel build --target preview` with this service config succeeded locally and authenticated/pushed the full image to VCR: `vcr.vercel.com/octopus-e236/retrace-visual-qa/retrace@sha256:58bf6eccf2530b7cd6622f34b74ac21f266e1e3f43b5deba6302bd44e565bf97`. This verifies account registry/container build access, not hosted Streamlit acceptance. New project Vercel Authentication was disabled (`ssoProtection:null`) for intended anonymous judge access; no portfolio/account-global change. Owner confirmed GitHub Login Connection completed; next preview must verify author attribution and runtime.

[WebSocket docs](https://vercel.com/kb/guide/do-vercel-serverless-functions-support-websocket-connections) native support public beta/all plans deyir. Session bir instance-a pin olunur; max duration-da connection bağlanır, reconnect fərqli instance-a gedə bilər. Immutable package persistence istəmir. Actual Streamlit hosted reconnect/media/download preview-də yoxlanmalıdır.

[Function limits](https://vercel.com/docs/functions/limitations): Hobby 2 GB/1 CPU, 300s; Pro/Enterprise max 4 GB/2 CPU, 800s (bəzi runtimes extended 1800s beta). Bunlar measured RETRACE requirement deyil. Latest local public image uncompressed **1,734,748,839 bytes (~1.62 GiB)**, image `sha256:5c801eaadc8777ff40d31133154d54b00362d09ec1dab013eb86a07dd6e28d08`, Python 3.12.15 / Streamlit 1.61.1. [Registry limits](https://vercel.com/kb/guide/how-to-use-vercel-container-registry): compressed layer 500 MB, image 15 GB. Production idle scale-down 5min, preview 30s, SIGTERM 30s grace; filesystem persistence gözlənilmir.

Standard Function response limit 4.5 MB; [streaming guidance](https://vercel.com/kb/guide/how-to-bypass-vercel-body-size-limit-serverless-functions) streaming responses istisnasını göstərir. Full 19.5 MB Streamlit download actual hosted acceptance gate-dir. External storage/another host/framework rewrite başlanmayıb.

## Actual verification

### Native Streamlit media adaptation

Container preview `dpl_5tpyKYm1HmZ6Kp3rrDeWtvFta5Rm` at `https://retrace-visual-r4bbxbd9m-octopus-e236.vercel.app` successfully loaded the Streamlit WebSocket/session and recorded FAIL/observations; health returned200. `/media/<id>.jpg` returned404 because instance-local media is unavailable to independently routed HTTP requests. This preview is not accepted as a complete application.

Minimal fix uses Streamlit [native static serving](https://docs.streamlit.io/develop/concepts/configuration/serving-static-files): Docker build copies exact `deploy/replay` bytes to `static/replay`, enables `STREAMLIT_SERVER_ENABLE_STATIC_SERVING=true` and `GAMEQA_PUBLIC_STATIC=1`. Public images/crops/diagnostics use `/app/static/replay/barrel/...`; a same-origin accessible anchor with `download` attribute serves the validated archive. Public runtime validates manifest/archive before showing the link. No external storage, framework replacement or runtime asset generation. Optional generated numbered overlays are omitted; original crops and box coordinates remain visible. Local/native downloads and approvals remain available outside this public static mode.

Hosted follow-up confirmed static PNG and full19.5MB ZIP endpoints work with exact hashes, but pinned Streamlit1.61 `st.image` converts same-origin absolute paths back into instance-local `/media` URLs. Static mode therefore renders escaped semantic HTML image/figure/caption directly; normal local `st.image` remains. This is a minimal compatibility correction, no evidence/image processing or design expansion.

Actual pinned Docker static browser: desktop/mobile/separate session and refresh pass; all6 original image/crop/diagnostic files decode; recorded observations and frozen config hash visible; fullZIP downloads with evidence.json and20/20manifest asset hashes matching; no console errors/overflow/provider requests. Focused UI20passed; full offline suite **218passed6deselected36.88s** (separate agent run218passed6skipped36.94s). Independent static adaptation review: NO BLOCKERS. Latest CLI63.1 container build/VCR upload succeeded, image `vcr.vercel.com/octopus-e236/retrace-visual-qa/retrace@sha256:d880245ca8be1f4da175ccda3bfd07318a3c8c3f86a5921844775144a66d1e43`; hosted acceptance pending.

```sh
env -u OPENROUTER_API_KEY GAMEQA_PUBLIC_REPLAY=1 PYTHONPATH=src PORT=8531 .venv/bin/python scripts/start_deployment.py
.venv/bin/python -m pytest -m 'not real_model' -q
```

- Latest offline suite: **212 passed, 6 deselected, 32.50s**; focused UI **14 passed**. Real-model checks excluded; no new inference.
- Independent review: all 20 original hashes, ZIP CRC/provenance, unchanged judgments/runtime identity pass; no credential patterns. Runtime reads existing archive bytes.
- Real Brave/CDP both local (Streamlit 1.65) and latest pinned Docker (1.61.1): desktop 1440×1000, mobile 390×844, separate Streamlit session 1280×900, refresh; FAIL/replay/export labels, originals/crops/observations/rules visible, images decoded, overflow0, console errors0, provider requests0. Download button transferred full19,478,122-byte ZIP; descriptor SHA exact, evidence.json FAIL, all20 original asset hashes match. Hosted checks pending.
- Ignored screenshots/results: `artifacts/retrace-ui-20261009/`. No key values logged.
- GitHub OAuth token lacks `workflow` scope. Proposed extra container CI job removed from unpublished commits; existing workflow unchanged. Existing offline/Render-container CI passed; public Docker separately built/browser-tested locally. No force push/bypass.
- New provider API calls **0**; inference cost **$0**. No paid hosting plan change. Hosted resource usage not yet measured.

## Remaining gates və rollback

1. Deploy preview, verify actual Streamlit session/FAIL/rules/observations/images/crops and full ZIP containing evidence.json. Match downloaded original assets to manifest hashes; verify refresh, separate anonymous session, desktop/mobile, no console errors/secrets/inference, cold start/reconnect.
2. Latest CI green + independent review, normal PR merge; deploy exact merged commit to production. Repeat HTTPS verification without Vercel login wall; record final URL, SHA/settings/results here.
3. Rollback: promote previous verified deployment in this RETRACE project; if none exists, disable the new deployment and fix on feature branch. Source changes through reviewed revert PR, no force push. Existing portfolio remains untouched.

If native hosted container/Streamlit/download fails, document exact platform error and request approval for the smallest alternative before architecture/hosting changes.
