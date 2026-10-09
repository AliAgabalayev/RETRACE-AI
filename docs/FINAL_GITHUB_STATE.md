# Final GitHub consolidation — C5

9 oktyabr 2026. Incoming baseline **feat/hackathon-demo-integration @68501897746bf674d582fd810cd9d7e2cfb943e6**. Frozen config **eaa371255716** dəyişmir. Bu sənəd merge üçün snapshot-dır; exact final default SHA final PR `mergeCommit` və final delivery ilə müəyyən edilir (commit öz gələcək merge SHA-sını daxil edə bilməz).

## Verified starting state

Fetch/prune icra edildi. Default **master @b7aa8b8a2155cdbe2f71f9598fd25c3f50ed5683**. Integration local/remote eyni, working tree clean idi. Ali HEAD **74f84cf23ff52530f47bbb280429ad6f5e9845ae**, runtime-eval **7e7bb5da2984e82b5910685a11fb826e9bf82efb**, docs/team-git-workflow **3fcab359fb12c781d095a6ec6266acc025038832**.

- PR #1 merged master; #2 closed historical draft.
- **PR #3 artıq integration-a merged**, 2026-10-09 12:53:20Z, **08267787e6cdd34502e1121975d4e8f60c3c07d0**. Ali report/global-change scope fix/tests ancestry-dədir; duplicate/stale imports edilmədi.
- Başlanğıc open PR və Actions runs yox idi. Master protected=false; protection endpoint 404, rulesets 403. Settings visibility/plan məhduddur; bypass/settings dəyişməsi edilmədi.
- Repository private, push permission var, admin yoxdur. Visibility dəyişmir.

## Consolidated work

Ali scope fix, storage evidence hook, OpenRouter config, C2 raw rows/docs, freeze/runbook, replay/rules/approval UI və tests qorunur. Native local ZIP/cache/history overwrite edilmir. Model/prompts/rules/alignment/proposals/crops/thresholds/policy/metrics dəyişmir.

C5: pinned headless runtime, Python 3.12, non-root Dockerfile/ignore, Streamlit config, exact DINO build cache, checksum-verified portable barrel replay, startup, missing-key Analyze guard/test, deployment/attribution docs və Linux CI. Vision/judge/prompts/report source dəyişdirilmədi. README active runtime OpenRouter-dır; Qwen historical baseline olaraq qalır.

## Delivery gate

Final integration PR normal merge üçün yaradılır; latest checks pass olmadan merge/force-push/branch deletion edilmir. Actual final SHA/PR state/checks final delivery-dədir. Incomplete check passing deyil. Public deployment owner addımıdır, `DEPLOYMENT.md` checklist təqdim edir.

C5 offline full suite **198 passed /6 deselected, 30.17 s**. İlk run-da src import path olmadan collection 1 error/6 deselected verdi; explicit PYTHONPATH ilə həmin suite keçdi, code tests üçün dəyişdirilmədi. Credential scan **262 tracked/new files**, secret hits 0, package-də Windows path 0. Git blob/manifest yoxlaması Windows CRLF normalization fərqini tapdı; replay package üçün `-text` attributes exact historical bytes saxlayır. Bu portability fix model davranışını dəyişmir.

C4 prior: **27 passed**, browser replay/rules/FAIL/crops/ZIP/guard, zero API calls. C2 prior: **186 passed /6 deselected**. Bunlar C5 fresh execution kimi təqdim edilmir. Local Docker daemon yoxdur; Linux CI həmin gap-i yoxlayır. C5 browser/CI nəticələri final delivery-dədir.

Known limits: 12-pair development diagnostic, both arms 41.7% coverage, hybrid 1/5 false-PASS, missing pedestal open. Historical 80 calls/$0.2871945. C5 paid inference **0**. Hosted measurements/access control/persistent storage manualdır.
