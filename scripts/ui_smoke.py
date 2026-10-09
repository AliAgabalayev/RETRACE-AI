"""Headless end-to-end UI smoke test of app.py with the REAL engines (no fakes).

Drives the Streamlit script through streamlit.testing.AppTest: pick a demo pair, Analyze,
check the verdict is rendered, rerun (must not re-run inference), then approve the candidate
as a new reference and check the history. This exercises app.py's logic, not a real browser.

Usage: .venv/bin/python scripts/ui_smoke.py [demo-pair-substring]   (default: object_removed)
Artifacts and references go to a temporary directory, so the repo stays untouched.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from streamlit.testing.v1 import AppTest

import gameqa.config as gc

REPO = Path(__file__).resolve().parents[1]


def main(pair_substring: str = "object_removed") -> int:
    tmp = Path(tempfile.mkdtemp(prefix="gameqa_ui_smoke_"))
    real_load = gc.load_config

    def load(path=None, overrides=None):  # redirect run outputs only; models/thresholds unchanged
        return real_load(path, {"run": {"artifacts_dir": str(tmp / "artifacts"),
                                        "references_dir": str(tmp / "references")},
                                **(overrides or {})})

    gc.load_config = load
    at = AppTest.from_file(str(REPO / "app.py"), default_timeout=600)
    at.run()
    assert not at.exception, at.exception
    next(r for r in at.radio if r.label == "Pair source").set_value("Demo pair").run()
    demo = next(s for s in at.selectbox if s.label == "Demo pair")
    name = next(o for o in demo.options if pair_substring in o)
    demo.set_value(name).run()
    next(b for b in at.button if b.label == "Analyze").click().run()
    assert not at.exception, at.exception

    runs = sorted((tmp / "artifacts").glob("*/analysis.json"))
    assert len(runs) == 1, f"expected 1 run, got {len(runs)}"
    result = json.loads(runs[0].read_text())
    page = " ".join(m.value for m in at.markdown) + " ".join(e.value for e in at.error) + \
        " ".join(s.value for s in at.success) + " ".join(w.value for w in at.warning)
    print(f"pair={name} decision={result['final_decision']} engine={result['engine_mode']}/"
          f"{result['execution_status']} regions={len(result['proposals'])}")
    assert result["final_decision"].replace("_", " ") in page or result["final_decision"] in page, \
        "decision not rendered on the page"

    # A plain rerun (e.g. widget interaction) must not trigger a new inference.
    at.run()
    assert len(list((tmp / "artifacts").glob("*/analysis.json"))) == 1, "rerun re-ran inference"

    # Explicit approval as a new reference (non-PASS runs need the extra override checkbox).
    for c in at.checkbox:
        c.check()
    at.run()
    for c in at.checkbox:  # the override checkbox appears only after the first one is ticked
        c.check()
    at.run()
    next(b for b in at.button if b.label == "Approve as new reference").click().run()
    assert not at.exception, at.exception
    histories = list((tmp / "references").glob("*/history.json"))
    assert histories, "approval did not write history.json"
    versions = sorted(p.name for p in histories[0].parent.glob("versions/*"))
    print(f"approved: {histories[0].parent.name} versions={versions}")
    assert len(versions) >= 2, "previous reference version was not preserved"
    print(f"UI smoke OK (outputs in {tmp})")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
