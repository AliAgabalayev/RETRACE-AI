"""Evidence sidecar + report sections, checked on a real exported ZIP (fake engines, no real VLM)."""

import hashlib
import json
import zipfile

from gameqa.contracts import Verdict
from gameqa.pipeline import analyze
from gameqa.report import build_evidence, render_report, write_evidence
from gameqa.storage import export_report, zip_path_for
from tests.app.conftest import FakeExtractor, FakeJudge, cfg, pair, patch_vision  # noqa: F401  (fixtures)


def _export(pair, cfg, judge):
    r = analyze(pair, cfg, judge=judge, extractor=FakeExtractor())
    run_dir = pair_dir(cfg, r)
    write_evidence(r, run_dir, cfg)  # until export_report calls it (see docs/ali/evidence_shape.md)
    export_report(r, run_dir)
    return r, run_dir


def pair_dir(cfg, r):
    from gameqa.storage import run_dir_for

    return run_dir_for(r.run_id, cfg)


def test_zip_contains_report_analysis_evidence_crops_images(pair, cfg, patch_vision):
    r, run_dir = _export(pair, cfg, FakeJudge(Verdict.FORBIDDEN, ["D1"]))
    names = set(zipfile.ZipFile(zip_path_for(run_dir)).namelist())
    for rel in ["report.md", "analysis.json", "evidence.json", "rules.yaml", "images/reference.png",
                "images/candidate.png", "images/aligned_candidate.png", "images/overlay.png",
                "crops/R1_ref.png", "crops/R1_cand.png"]:
        assert f"{r.run_id}/{rel}" in names, rel


def test_evidence_content_from_unzipped_export(pair, cfg, patch_vision, tmp_path):
    r, run_dir = _export(pair, cfg, FakeJudge(Verdict.FORBIDDEN, ["D1"]))
    out = tmp_path / "unzipped"
    zipfile.ZipFile(zip_path_for(run_dir)).extractall(out)
    root = out / r.run_id
    ev = json.loads((root / "evidence.json").read_text())

    ref = ev["inputs"]["reference"]
    assert ref["sha256"] == hashlib.sha256((root / "images/reference.png").read_bytes()).hexdigest()
    assert (ref["width"], ref["height"]) == (160, 120)
    reg = ev["regions"][0]
    assert reg["box"] == [30, 20, 80, 60] and reg["verdict"] == "forbidden"
    assert reg["expected_rules"][0]["id"] == "D1" and reg["expected_rules"][0]["effect"] == "deny"
    assert reg["observed_change_vlm_reported"] == "something changed"
    assert reg["reference_crop"]["sha256"] and reg["candidate_crop"]["path"] == "crops/R1_cand.png"
    assert ev["decision"]["final"] == "FAIL" and ev["decision"]["reason"]
    assert ev["identity"]["vlm_model"] == "fake:test" and ev["identity"]["prompt_version"] == "vtest"
    assert ev["identity"]["config_hash"]
    assert ev["cache"]["status"] == "unknown (replay possible)"
    assert "live" not in ev["cache"]["status"]
    assert ev["scope"]["scene_audit_ran"] is True


def test_report_sections_and_no_invented_repro(pair, cfg, patch_vision):
    r, run_dir = _export(pair, cfg, FakeJudge())
    text = (run_dir / "report.md").read_text()
    for needle in ["## Input IDs", "## Scope", "## Model identity and cache", "unknown (replay possible)",
                   "vtest", "fake:test", "evidence.json"]:
        assert needle in text, needle
    assert "root cause" in text and "reproduction steps" in text  # stated as unknown, not invented
    assert "build id" not in text.lower()


def test_run_dir_gives_hashes_in_report(pair, cfg, patch_vision):
    r, run_dir = _export(pair, cfg, FakeJudge())
    with_dir = render_report(r, run_dir)
    sha = hashlib.sha256((run_dir / "images/candidate.png").read_bytes()).hexdigest()
    assert sha in with_dir
    assert "not computed" in render_report(r)


def test_scope_reports_truncation_and_missing_audit(pair, cfg, patch_vision):
    patch_vision["coverage"].proposals_total = 3
    patch_vision["coverage"].truncated = True
    r = analyze(pair, cfg, judge=FakeJudge(), extractor=FakeExtractor())
    ev = build_evidence(r)
    assert any("dropped by the region cap" in n for n in ev["scope"]["not_assessed"])
    assert ev["scope"]["truncated"] is True


def test_mock_engine_cache_not_applicable(pair, cfg, patch_vision):
    r = analyze(pair, cfg, judge=FakeJudge(is_mock=True), extractor=FakeExtractor())
    assert "mock" in build_evidence(r)["cache"]["status"]


def test_cache_disabled_in_config_is_live(pair, cfg, patch_vision):
    r = analyze(pair, cfg, judge=FakeJudge(), extractor=FakeExtractor())
    cfg["vlm"]["cache"] = False
    cfg["vlm"]["reasoning_effort"] = "low"
    ev = build_evidence(r, None, cfg)
    assert ev["cache"]["status"].startswith("live") and ev["identity"]["reasoning_effort"] == "low"


def test_plain_export_report_writes_evidence(pair, cfg, patch_vision):
    r = analyze(pair, cfg, judge=FakeJudge(), extractor=FakeExtractor())
    run_dir = pair_dir(cfg, r)
    export_report(r, run_dir)
    assert f"{r.run_id}/evidence.json" in zipfile.ZipFile(zip_path_for(run_dir)).namelist()
