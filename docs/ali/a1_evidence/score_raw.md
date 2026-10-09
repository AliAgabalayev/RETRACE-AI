# A1 score (real)

WARNING: label file mtime 2026-10-09T11:38:35+00:00 is NEWER than the first prediction 2026-10-09T11:21:24+00:00: labels may not have been frozen before outputs.

Targets (engineering targets, not promised results): 10/12 correct primary observations; 0/6 bug false-PASS; >=4/6 clean PASS; coverage >=6/12.
Target flags are only evaluated for n=12 (observations, coverage); at n=6 compare counts by hand. `unknown` = not computable yet.

| arm | rows | PASS/FAIL/REVIEW | coverage | obs correct | bug false-PASS | clean PASS | truncation causes | classes |
|---|---|---|---|---|---|---|---|---|
| A | 12 | 12/0/0 | 12/12 | None | 5/5 | 7/7 | None | {'ok': 7, 'unscored': 5} |
| B | 12 | 8/0/4 | 8/12 | 0/0 marked 'y' of 12 rows (0 marked) | 5/5 | 3/7 | {'none': 12} | {'ok': 3, 'unscored': 9} |
| C | 12 | 0/0/12 | 0/12 | 0/0 marked 'y' of 12 rows (0 marked) | 0/5 | 0/7 | {'global_change_collapse': 9, 'none': 3} | {'unscored': 12} |

## Arm A cases

| sample | truth | decision | class | flags | obs | truncation | OOS | cache | error |
|---|---|---|---|---|---|---|---|---|---|
| vr_a981c1d3 | clean | PASS | ok |  | None | None | N | None | None |
| vr_330651ed | bug | PASS | unscored |  | None | None | N | None | None |
| vr_4255ae09 | clean | PASS | ok |  | None | None | N | None | None |
| vr_4b921c5d | bug | PASS | unscored |  | None | None | N | None | None |
| vr_d07179d5 | bug | PASS | unscored |  | None | None | N | None | None |
| vr_fec26436 | bug | PASS | unscored |  | None | None | N | None | None |
| vr_09a066d3 | clean | PASS | ok |  | None | None | N | None | None |
| vr_59af7164 | clean | PASS | ok |  | None | None | N | None | None |
| vr_41bab231 | clean | PASS | ok |  | None | None | N | None | None |
| vr_c1f47c57 | bug | PASS | unscored |  | None | None | N | None | None |
| vr_ef9b073a | clean | PASS | ok |  | None | None | N | None | None |
| vr_43773eb8 | clean | PASS | ok |  | None | None | N | None | None |

## Arm B cases

| sample | truth | decision | class | flags | obs | truncation | OOS | cache | error |
|---|---|---|---|---|---|---|---|---|---|
| vr_a981c1d3 | clean | PASS | ok |  | None | None | N | fresh | None |
| vr_330651ed | bug | PASS | unscored |  | None | None | N | fresh | None |
| vr_4255ae09 | clean | PASS | ok |  | None | None | N | fresh | None |
| vr_4b921c5d | bug | PASS | unscored |  | None | None | N | fresh | None |
| vr_d07179d5 | bug | PASS | unscored |  | None | None | N | fresh | None |
| vr_fec26436 | bug | PASS | unscored |  | None | None | N | fresh | None |
| vr_09a066d3 | clean | PASS | ok |  | None | None | N | fresh | None |
| vr_59af7164 | clean | NEEDS_REVIEW | unscored |  | None | None | N | fresh | None |
| vr_41bab231 | clean | NEEDS_REVIEW | unscored |  | None | None | N | fresh | None |
| vr_c1f47c57 | bug | PASS | unscored |  | None | None | N | fresh | None |
| vr_ef9b073a | clean | NEEDS_REVIEW | unscored |  | None | None | N | fresh | None |
| vr_43773eb8 | clean | NEEDS_REVIEW | unscored |  | None | None | N | fresh | None |

## Arm C cases

| sample | truth | decision | class | flags | obs | truncation | OOS | cache | error |
|---|---|---|---|---|---|---|---|---|---|
| vr_a981c1d3 | clean | NEEDS_REVIEW | unscored |  | None | global_change_collapse | N | fresh | None |
| vr_330651ed | bug | NEEDS_REVIEW | unscored |  | None | global_change_collapse | N | fresh | None |
| vr_4255ae09 | clean | NEEDS_REVIEW | unscored |  | None | global_change_collapse | N | fresh | None |
| vr_4b921c5d | bug | NEEDS_REVIEW | unscored |  | None | None | N | fresh | None |
| vr_d07179d5 | bug | NEEDS_REVIEW | unscored |  | None | None | N | fresh | None |
| vr_fec26436 | bug | NEEDS_REVIEW | unscored |  | None | global_change_collapse | N | fresh | None |
| vr_09a066d3 | clean | NEEDS_REVIEW | unscored |  | None | global_change_collapse | N | fresh | None |
| vr_59af7164 | clean | NEEDS_REVIEW | unscored |  | None | global_change_collapse | N | fresh | None |
| vr_41bab231 | clean | NEEDS_REVIEW | unscored |  | None | global_change_collapse | N | fresh | None |
| vr_c1f47c57 | bug | NEEDS_REVIEW | unscored |  | None | None | N | fresh | None |
| vr_ef9b073a | clean | NEEDS_REVIEW | unscored |  | None | global_change_collapse | N | fresh | None |
| vr_43773eb8 | clean | NEEDS_REVIEW | unscored |  | None | global_change_collapse | N | fresh | None |
