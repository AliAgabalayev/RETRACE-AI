"""Paired comparison of E1/E2/E4 on the same 60 IDs (CPU only, no model calls).

Usage: python3 scripts/compare_runs.py [--n-boot 10000] [--seed 0]
Primary metric: balanced accuracy, review->FAIL (flag = decision != PASS).
Paired stratified percentile bootstrap: bug and no_bug IDs resampled with replacement
(same resampled IDs for both methods), difference of balanced accuracy.
Safety metric: false PASS on bug pairs (decision == PASS), Wilson 95% CI.
"""
import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from math import comb

ROOT = Path(__file__).resolve().parents[1]
RUNS = {
    "E1": ROOT / "artifacts/eval/e1_classical_eval_subset60/predictions.jsonl",
    "E2": ROOT / "artifacts/eval/e2_pipeline_subset60/predictions.jsonl",
    "E4": ROOT / "artifacts/eval/e4_vlm_only_subset60/predictions.jsonl",
}
LABELS = ROOT / "data/manifests/eval_labels.json"
IDS = ROOT / "data/manifests/eval_subset_60.json"


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def ba(pairs):
    """pairs: list of (truth, decision). Balanced accuracy, review->FAIL."""
    bug = [d for t, d in pairs if t == "bug"]
    nob = [d for t, d in pairs if t == "no_bug"]
    if not bug or not nob:
        return None
    return (sum(d != "PASS" for d in bug) / len(bug) + sum(d == "PASS" for d in nob) / len(nob)) / 2


def pct(vals, q):
    vals = sorted(vals)
    return vals[min(len(vals) - 1, max(0, int(q * len(vals))))]


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    labels = json.load(open(LABELS))
    ids = json.load(open(IDS))
    dec, src = {}, {}
    for name, p in RUNS.items():
        dec[name] = {}
        for line in open(p):
            r = json.loads(line)
            dec[name][r["sample_id"]] = "NEEDS_REVIEW" if r.get("error") else r["decision"]
            src[r["sample_id"]] = r["media_source"]
        assert set(dec[name]) == set(ids), name
    truth = {i: labels[i]["label"] for i in ids}
    bug_ids = [i for i in ids if truth[i] == "bug"]
    nob_ids = [i for i in ids if truth[i] == "no_bug"]
    out = {"n": len(ids), "n_bug": len(bug_ids), "n_no_bug": len(nob_ids), "methods": {}, "contrasts": {}}

    print(f"N={len(ids)} bug={len(bug_ids)} no_bug={len(nob_ids)}  n_boot={a.n_boot} seed={a.seed}\n")
    print("== Per method (review->FAIL) ==")
    for m in RUNS:
        d = dec[m]
        pairs = [(truth[i], d[i]) for i in ids]
        fp = sum(d[i] == "PASS" for i in bug_ids)
        lo, hi = wilson(fp, len(bug_ids))
        fl_nb = sum(d[i] != "PASS" for i in nob_ids)
        rev = sum(d[i] == "NEEDS_REVIEW" for i in ids)
        # bootstrap CI of own BA
        rng = random.Random(a.seed)
        vals = []
        for _ in range(a.n_boot):
            b = [rng.choice(bug_ids) for _ in bug_ids]
            n = [rng.choice(nob_ids) for _ in nob_ids]
            vals.append(ba([("bug", d[i]) for i in b] + [("no_bug", d[i]) for i in n]))
        row = {"ba": ba(pairs), "ba_ci": [pct(vals, .025), pct(vals, .975)],
               "false_pass_bug": fp, "false_pass_rate": fp / len(bug_ids), "false_pass_ci": [lo, hi],
               "no_bug_flagged": fl_nb, "review": rev, "review_rate": rev / len(ids),
               "decisions": {k: sum(d[i] == k for i in ids) for k in ("PASS", "FAIL", "NEEDS_REVIEW")}}
        by = defaultdict(list)
        for i in ids:
            by[src[i]].append(i)
        row["per_source"] = {}
        for s, ii in sorted(by.items()):
            bb = [i for i in ii if truth[i] == "bug"]
            nn = [i for i in ii if truth[i] == "no_bug"]
            f = sum(d[i] == "PASS" for i in bb)
            l, h = wilson(f, len(bb))
            row["per_source"][s] = {"n_bug": len(bb), "n_no_bug": len(nn), "false_pass": f,
                                    "false_pass_ci": [l, h],
                                    "ba": ba([(truth[i], d[i]) for i in ii]),
                                    "no_bug_flagged": sum(d[i] != "PASS" for i in nn),
                                    "review": sum(d[i] == "NEEDS_REVIEW" for i in ii)}
        out["methods"][m] = row
        print(f"{m}: BA={row['ba']:.4f} CI[{row['ba_ci'][0]:.4f},{row['ba_ci'][1]:.4f}] decisions={row['decisions']} "
              f"falsePASS={fp}/{len(bug_ids)}={fp/len(bug_ids):.3f} Wilson[{lo:.3f},{hi:.3f}] "
              f"no_bug_flagged={fl_nb}/{len(nob_ids)} review_rate={rev/len(ids):.3f}")
        for s, v in row["per_source"].items():
            print(f"    {s}: bug={v['n_bug']} no_bug={v['n_no_bug']} falsePASS={v['false_pass']}/{v['n_bug']} "
                  f"Wilson[{v['false_pass_ci'][0]:.3f},{v['false_pass_ci'][1]:.3f}] BA={v['ba']} "
                  f"no_bug_flagged={v['no_bug_flagged']} review={v['review']}")

    print("\n== Paired contrasts (A minus B), balanced accuracy review->FAIL ==")
    for A, B in (("E2", "E1"), ("E2", "E4"), ("E4", "E1")):
        dA, dB = dec[A], dec[B]
        point = ba([(truth[i], dA[i]) for i in ids]) - ba([(truth[i], dB[i]) for i in ids])
        rng = random.Random(a.seed)
        diffs = []
        for _ in range(a.n_boot):
            b = [rng.choice(bug_ids) for _ in bug_ids]
            n = [rng.choice(nob_ids) for _ in nob_ids]
            pa = [("bug", dA[i]) for i in b] + [("no_bug", dA[i]) for i in n]
            pb = [("bug", dB[i]) for i in b] + [("no_bug", dB[i]) for i in n]
            diffs.append(ba(pa) - ba(pb))
        ci95 = [pct(diffs, .025), pct(diffs, .975)]
        ci98 = [pct(diffs, .05 / 3 / 2), pct(diffs, 1 - .05 / 3 / 2)]  # Bonferroni for 3 contrasts
        # discordant false-PASS on bug pairs
        b_ = sum(dA[i] == "PASS" and dB[i] != "PASS" for i in bug_ids)  # A pass, B not
        c_ = sum(dA[i] != "PASS" and dB[i] == "PASS" for i in bug_ids)
        p = mcnemar_exact(b_, c_)
        # cutscene-only BA diff (only source with both classes)
        cut = [i for i in ids if src[i] == "Youtube-Cutscene"]
        cpoint = ba([(truth[i], dA[i]) for i in cut]) - ba([(truth[i], dB[i]) for i in cut])
        out["contrasts"][f"{A}-{B}"] = {"diff": point, "ci95": ci95, "ci_bonf3": ci98,
                                        "false_pass_discordant": {f"{A}_pass_{B}_not": b_, f"{B}_pass_{A}_not": c_},
                                        "mcnemar_exact_p": p, "cutscene_only_diff": cpoint}
        print(f"{A}-{B}: diff={point:+.4f} 95%CI[{ci95[0]:+.4f},{ci95[1]:+.4f}] Bonf3 98.3%CI[{ci98[0]:+.4f},{ci98[1]:+.4f}] "
              f"| bug false-PASS discordant: {A} PASS/{B} not={b_}, {B} PASS/{A} not={c_}, exact McNemar p={p:.2g} "
              f"| cutscene-only BA diff={cpoint:+.4f}")
    (ROOT / "artifacts/eval/paired_comparison.json").write_text(json.dumps(out, indent=2))
    print("\nwrote artifacts/eval/paired_comparison.json")


if __name__ == "__main__":
    main()
