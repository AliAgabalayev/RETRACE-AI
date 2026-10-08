"""Hand-computed checks of scripts/evaluate.py scoring (denominators, mappings)."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("evaluate", Path(__file__).resolve().parents[2] / "scripts" / "evaluate.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)

ROWS = ([("bug", "FAIL")] * 5 + [("bug", "NEEDS_REVIEW")] * 2 + [("bug", "PASS")] * 1
        + [("no_bug", "PASS")] * 3 + [("no_bug", "FAIL")] * 1 + [("no_bug", "NEEDS_REVIEW")] * 2)


def test_counts_and_denominators():
    m = ev.metrics_for(ROWS)
    assert m["n"] == 14 and m["n_bug"] == 8 and m["n_no_bug"] == 6
    assert m["confusion_matrix"]["bug"] == {"PASS": 1, "FAIL": 5, "NEEDS_REVIEW": 2}
    assert m["review_rate"] == round(4 / 14, 4) and m["decision_coverage"] == round(10 / 14, 4)
    assert m["decided_pair_accuracy"] == round(8 / 10, 4)  # 5 FAIL on bug + 3 PASS on no_bug


def test_review_mappings():
    m = ev.metrics_for(ROWS)
    f = m["review_to_fail"]  # positive = FAIL|REVIEW: tp=7 fp=3 ; recall 7/8, no_bug recall 3/6
    assert (f["tp"], f["fp"], f["bug_recall"], f["no_bug_recall"]) == (7, 3, 0.875, 0.5)
    assert f["bug_precision"] == 0.7 and f["balanced_accuracy"] == round((0.875 + 0.5) / 2, 4)
    p = m["review_to_pass"]  # positive = FAIL: tp=5 fp=1 ; bug recall 5/8, no_bug recall 5/6
    assert (p["tp"], p["fp"], p["bug_recall"]) == (5, 1, 0.625) and p["no_bug_recall"] == round(5 / 6, 4)
    x = m["review_excluded"]  # review dropped: bug 6 decided, no_bug 4 decided
    assert x["excluded_review"] == 4 and x["bug_recall"] == round(5 / 6, 4) and x["no_bug_recall"] == 0.75


def test_always_rows_are_half():
    r = ev.reference_rows(["bug"] * 9 + ["no_bug"])
    assert r["always_FAIL"]["balanced_accuracy_review_to_fail"] == 0.5
    assert r["always_PASS"]["balanced_accuracy_review_to_pass"] == 0.5
    assert r["always_NEEDS_REVIEW"]["balanced_accuracy_review_to_fail"] == 0.5
