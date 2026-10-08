"""Headless Streamlit checks (AppTest). Engines are fakes; mock mode is exercised for banners."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from gameqa import pipeline
from gameqa.contracts import Verdict

from .conftest import FakeExtractor, FakeJudge


@pytest.fixture
def app(cfg, patch_vision, monkeypatch, tmp_path):
    import gameqa.config as gc

    calls = {"n": 0}
    real_load = gc.load_config

    def load(path=None, overrides=None):
        return real_load(path, {"run": {"artifacts_dir": str(tmp_path / "artifacts"),
                                        "references_dir": str(tmp_path / "references")},
                                **(overrides or {})})

    monkeypatch.setattr(gc, "load_config", load)
    judge = FakeJudge(Verdict.FORBIDDEN, ["D1"])

    def engines(c):
        calls["n"] += 1
        return FakeExtractor(), judge

    monkeypatch.setattr(pipeline, "build_engines", engines)
    at = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"), default_timeout=30)
    at.calls = calls
    return at


def test_demo_analyze_does_not_rerun_inference(app, tmp_path):
    app.run()
    assert not app.exception
    [r for r in app.radio if r.label == "Pair source"][0].set_value("Demo pair").run()
    if "synthetic fixture | object_removed" not in app.selectbox[-1].options:
        pytest.skip("fixture not available")
    app.selectbox[-1].set_value("synthetic fixture | object_removed").run()
    app.button[0].click().run()
    assert not app.exception, app.exception
    banners = [e.value for e in list(app.error) + list(app.warning) + list(app.success)]
    assert any(b.startswith("**FAIL") for b in banners), banners
    judge_calls = app.calls["n"]
    app.run()  # plain rerun
    assert app.calls["n"] == judge_calls
    app.button[0].click().run()  # same inputs again -> cached run
    assert app.calls["n"] == judge_calls
    assert len(list((tmp_path / "artifacts").glob("*/analysis.json"))) == 1
