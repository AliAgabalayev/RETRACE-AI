"""Streamlit UI for the rule-aware visual regression prototype.

Run: .venv/bin/streamlit run app.py
Inference runs only when Analyze is pressed; results are kept in st.session_state
(keyed by an input hash) and on disk, so Streamlit reruns never repeat inference.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from gameqa import pipeline
from gameqa.config import REPO_ROOT, config_hash, load_config, load_env_file
from gameqa.contracts import AnalysisResult, FinalDecision, PairInput
from gameqa.report import draw_boxes
from gameqa.rules import RulesError, dump_rules, load_rules, rules_from_dicts
from gameqa.storage import (
    StorageError, approve_reference, export_report, list_runs, load_run, run_dir_for, zip_path_for,
)

MOCK_BEHAVIORS = ["allowed", "forbidden", "uncertain", "timeout", "invalid_json", "unknown_rule"]
MANIFEST = REPO_ROOT / "data" / "manifests" / "inference_manifest.json"
FIXTURES = REPO_ROOT / "data" / "fixtures"
EXAMPLE_RULES = REPO_ROOT / "configs" / "rules_example.yaml"
DEMO_BUNDLE = REPO_ROOT / "artifacts" / "c1-demo-20261009"
FROZEN_DEMO_IDS = {"vr_4b921c5d", "vr_09a066d3", "vr_330651ed"}

st.set_page_config(page_title="Game Visual QA", layout="wide")


# ---------- cached resources and helpers ----------
@st.cache_resource(show_spinner="Loading models (first run only)...")
def get_engines(cfg_key: str, mock_behavior: str | None):
    return pipeline.build_engines(make_config(mock_behavior))


def reload_engines_button() -> None:
    """Engines are cached per process; after a model load failure, this retries without a restart."""
    if st.sidebar.button("Reload models", help="Clear cached DINOv2/VLM engines and load them again"):
        get_engines.clear()
        st.sidebar.success("Model cache cleared; the next Analyze reloads them.")


def make_config(mock_behavior: str | None) -> dict:
    if mock_behavior:
        return load_config(overrides={"vlm": {"provider": "mock", "mock_behavior": mock_behavior}})
    return load_config()


def demo_pairs() -> dict[str, dict]:
    pairs: dict[str, dict] = {}
    inventory = DEMO_BUNDLE / "inventory.json"
    if inventory.is_file():
        for sample in json.loads(inventory.read_text(encoding="utf-8"))["samples"]:
            sid = sample["sample_id"]
            if sid not in FROZEN_DEMO_IDS:
                continue
            ref, cand = DEMO_BUNDLE / "bundle" / sid / "reference.png", DEMO_BUNDLE / "bundle" / sid / "candidate.png"
            if ref.is_file() and cand.is_file():
                pairs[f"Frozen dev demo | {sid}"] = {
                    "ref": ref, "cand": cand, "rules": sample["rules"], "sample_id": sid,
                    "hashes": sample["images"],
                }
    if MANIFEST.is_file():
        for m in json.loads(MANIFEST.read_text(encoding="utf-8")):
            if m.get("split") == "demo":
                ref, cand = REPO_ROOT / m["reference_path"], REPO_ROOT / m["candidate_path"]
                if not (ref.is_file() and cand.is_file()):
                    continue  # Unavailable media must not be selectable in the demo UI.
                pairs[f"VideoGameQA-Bench | {m['sample_id']}"] = {
                    "ref": ref, "cand": cand,
                    "rules": m.get("rules", []), "sample_id": m["sample_id"],
                }
    if FIXTURES.is_dir():
        for d in sorted(FIXTURES.iterdir()):
            if (d / "reference.png").is_file() and (d / "candidate.png").is_file():
                rules = []
                if (d / "rules.yaml").is_file():
                    try:
                        rules = [r.model_dump(mode="json") for r in load_rules(d / "rules.yaml")]
                    except RulesError:
                        rules = []
                pairs[f"synthetic fixture | {d.name}"] = {
                    "ref": d / "reference.png", "cand": d / "candidate.png", "rules": rules,
                    "sample_id": f"fixture_{d.name}",
                }
    return pairs


def input_hash(ref: bytes, cand: bytes, rules_yaml: str, mock: str | None) -> str:
    h = hashlib.sha256()
    for part in (ref, cand, rules_yaml.encode(), config_hash(make_config(mock)).encode()):
        h.update(hashlib.sha256(part).digest())
    return h.hexdigest()


def rules_editor(initial: list[dict], key: str):
    df = pd.DataFrame(initial or [], columns=["id", "effect", "description"]).astype(str)
    edited = st.data_editor(
        df, key=f"rules_{key}", num_rows="dynamic", width="stretch",
        column_config={"effect": st.column_config.SelectboxColumn("effect", options=["allow", "deny"], required=True)},
    )
    items = [r for r in edited.to_dict("records") if any(str(v).strip() for v in r.values())]
    try:
        return rules_from_dicts(items), None
    except RulesError as exc:
        return None, str(exc)


def img(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"))


# ---------- result rendering ----------
def evidence_zip(result: AnalysisResult, run_dir: Path) -> bytes:
    """Reuse a matching saved export; reruns must preserve original evidence ZIPs."""
    path = zip_path_for(run_dir)
    if path.is_file():
        data = path.read_bytes()
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                prefix = f"{result.run_id}/"
                analysis = json.loads(archive.read(prefix + "analysis.json"))
                evidence = json.loads(archive.read(prefix + "evidence.json"))
                archive.getinfo(prefix + "report.md")
                if (analysis["run_id"] == result.run_id
                        and analysis["final_decision"] == result.final_decision.value
                        and evidence["decision"]["final"] == result.final_decision.value):
                    return data
        except (KeyError, ValueError, zipfile.BadZipFile):
            pass
    export_report(result, run_dir)
    return path.read_bytes()


def render_result(result: AnalysisResult, run_dir: Path) -> None:
    dec = result.final_decision
    label = dec.value.replace("_", " ")
    banner = {FinalDecision.PASS: st.success, FinalDecision.FAIL: st.error,
              FinalDecision.NEEDS_REVIEW: st.warning}[dec]
    banner(f"**{label}**: {result.decision_reason}")
    st.caption(f"Sample: {result.sample_id or 'uploaded pair'} | Run: {result.run_id}")
    if result.engine_mode == "mock":
        st.error("MOCK ENGINE: these judgments are fake and are NOT real model inference.")
    elif result.engine_mode == "degraded":
        st.warning("DEGRADED: a model component was unavailable or returned errors "
                   "(see Diagnostics). Result is not a full AI run.")
    else:
        st.caption(f"Engine: real ({result.versions.vlm_model or 'no model needed'})")

    ref_p, cand_p = run_dir / "images/reference.png", run_dir / "images/candidate.png"
    if ref_p.is_file() and cand_p.is_file():
        ref, cand = img(ref_p), img(cand_p)
        a = result.alignment
        use_inv = a is not None and a.status.value in ("aligned", "resized")
        cand_boxes = draw_boxes(cand, result.proposals, a.candidate_to_reference if use_inv else None)
        c1, c2 = st.columns(2)
        c1.image(draw_boxes(ref, result.proposals), caption="Reference (numbered change proposals)")
        c2.image(cand_boxes, caption="Candidate" + (
            " (boxes mapped back through the inverse alignment)" if use_inv
            else " (boxes in reference coordinates; no alignment transform applied)"))

    st.subheader("Regions")
    if not result.judgments:
        st.write("No regions were judged.")
    judged = {j.region_id: j for j in result.judgments}
    for p in result.proposals:
        j = judged.get(p.id)
        verdict = j.verdict.value if j else "not judged"
        with st.expander(f"{p.id}: {verdict}  box={list(p.box)}  source={p.source}"):
            cc1, cc2 = st.columns(2)
            for col, suffix, cap in ((cc1, "ref", "Reference crop"), (cc2, "cand", "Candidate crop (aligned)")):
                f = run_dir / f"crops/{p.id}_{suffix}.png"
                if f.is_file():
                    col.image(str(f), caption=cap)
            if j:
                st.markdown(f"**Observed:** {j.observed_change or 'n/a'}")
                st.markdown(f"**Rules:** {', '.join(j.rule_ids) or 'none cited'}")
                st.markdown(f"**Evidence:** {j.evidence or 'n/a'}")
                st.caption(f"Model: {j.model}{' (MOCK)' if j.is_mock else ''} | validated: {j.validated}")
                if j.errors:
                    st.error("; ".join(j.errors))

    st.subheader("Whole-scene audit")
    if result.scene_audit:
        aj = result.scene_audit.judgment
        st.markdown(f"**{aj.verdict.value}**: {aj.observed_change or 'n/a'}")
        st.markdown(f"Rules: {', '.join(aj.rule_ids) or 'none'} | Evidence: {aj.evidence or 'n/a'}")
        if result.scene_audit.extra_changes_reported:
            st.warning("The audit reported changes outside the proposed regions.")
        if aj.errors:
            st.error("; ".join(aj.errors))
    else:
        st.info("Scene audit did not run.")

    with st.expander("Diagnostics"):
        a = result.alignment
        st.write(f"Alignment: {a.status.value if a else 'n/a'}"
                 + (f" (overlap {a.overlap_fraction:.2f})" if a else ""))
        st.json({"coverage": result.coverage.model_dump(), "timings_s": result.timings,
                 "versions": result.versions.model_dump(), "execution_status": result.execution_status.value,
                 "errors": result.errors})
        for rel, cap in (("diagnostics/heatmap.png", "DINOv2 distance heatmap"),
                         ("diagnostics/overlap_mask.png", "Alignment overlap mask")):
            if (run_dir / rel).is_file():
                st.image(str(run_dir / rel), caption=cap)
        st.caption(f"Run ID {result.run_id} | saved in {run_dir}")

    st.subheader("Actions")
    st.download_button("Download evidence ZIP", evidence_zip(result, run_dir),
                       file_name=f"{result.run_id}.zip", mime="application/zip",
                       key=f"export_{result.run_id}", on_click="ignore")
    render_approval(result, run_dir)


def render_approval(result: AnalysisResult, run_dir: Path) -> None:
    default_id = re.sub(r"[^A-Za-z0-9_.-]", "_", result.sample_id or "")
    open_key = f"approval_open_{result.run_id}"
    def keep_open():
        st.session_state[open_key] = True

    with st.expander("Approve as new reference", expanded=st.session_state.get(open_key, False)):
        st.write("Stores this candidate as a new version of the reference. Older versions are kept.")
        ref_id = st.text_input("Reference ID", value=default_id, key=f"refid_{result.run_id}",
                               on_change=keep_open)
        sure = st.checkbox("I confirm this candidate becomes the new reference",
                           key=f"confirm_{result.run_id}", on_change=keep_open)
        risky = result.final_decision.value != "PASS" or result.engine_mode != "real"
        if risky:
            st.warning(f"This run is {result.final_decision.value} (engine: {result.engine_mode}). "
                       "Approving overrides the tool's verdict.")
            override = st.checkbox("I reviewed the regions and override the verdict",
                                   key=f"override_{result.run_id}", on_change=keep_open)
            sure = sure and override
        if st.button("Approve as new reference", disabled=not (sure and ref_id.strip()),
                     key=f"approve_{result.run_id}"):
            try:
                info = approve_reference(
                    ref_id.strip(), run_dir / "images/candidate.png", result.run_id, load_config(),
                    previous_reference_path=run_dir / "images/reference.png")
                st.success(f"Previous version: {info['previous_version']} -> new version: "
                           f"{info['new_version']} ({info['reference_id']})")
            except (StorageError, ValueError) as exc:
                st.error(f"Approval failed: {exc}")


# ---------- main ----------
def main() -> None:
    st.title("Game Visual QA")
    st.caption("Compare approved and new-build screenshots against your rules, with visual evidence.")
    st.caption("PASS: no forbidden change found · FAIL: forbidden change reported · "
               "NEEDS_REVIEW: uncertain or incomplete assessment. "
               "Development diagnostic; uncertain cases go to human review.")
    cfg_default = load_config()
    load_env_file()
    state = st.session_state
    state.setdefault("runs_by_hash", {})

    reload_engines_button()
    with st.sidebar:
        st.header("Engine")
        st.caption(f"Configured: {cfg_default['vlm']['model']} | "
                   f"{cfg_default['vlm']['base_url'].split('//')[-1].split('/')[0]}")
        engine = st.radio("VLM engine", ["Real (config)", "MOCK (fault injection)"],
                          help="MOCK output is fake and never counts as real inference.")
        mock = None
        if engine.startswith("MOCK"):
            mock = st.selectbox("Mock behavior", MOCK_BEHAVIORS)
            st.error("MOCK engine selected: results are not real inference.")
        st.header("Saved runs")
        runs = list_runs(cfg_default)
        if runs:
            choice = st.selectbox(
                "Open a saved run", [r["run_id"] for r in runs],
                format_func=lambda rid: next(f"{r['final_decision']} | {r['sample_id'] or '-'} | {rid}"
                                             for r in runs if r["run_id"] == rid))
            if st.button("Load saved run"):
                state["active_run_id"] = choice
                state["active_mode"] = "replay"
        else:
            st.caption("No saved runs yet.")

    if state.get("active_mode") == "replay" and state.get("active_run_id"):
        if st.button("Compare new screenshots"):
            state.pop("active_run_id", None)
            state.pop("active_mode", None)
            st.rerun()
        st.info("Saved run replay — no new inference")
        try:
            active = state["active_run_id"]
            result = load_run(active, cfg_default)
            st.subheader("Rules stored with this run (read-only)")
            st.dataframe(pd.DataFrame([r.model_dump(mode="json") for r in result.rules],
                                      columns=["id", "effect", "description"]),
                         hide_index=True, width="stretch")
            render_result(result, run_dir_for(active, cfg_default))
        except StorageError as exc:
            st.error(f"Cannot load run {active}: {exc}")
        return

    source = st.radio("Pair source", ["Upload two images", "Demo pair"], horizontal=True)
    ref_bytes = cand_bytes = None
    initial_rules: list[dict] = []
    sample_id = None
    ref_path = cand_path = None
    if source == "Upload two images":
        u1, u2 = st.columns(2)
        up_ref = u1.file_uploader("Reference (approved screenshot)", type=["png", "jpg", "jpeg", "webp", "bmp"])
        up_cand = u2.file_uploader("Candidate (new build screenshot)", type=["png", "jpg", "jpeg", "webp", "bmp"])
        if up_ref and up_cand:
            ref_bytes, cand_bytes = up_ref.getvalue(), up_cand.getvalue()
        if EXAMPLE_RULES.is_file():
            initial_rules = [r.model_dump(mode="json") for r in load_rules(EXAMPLE_RULES)]
        src_key = "upload"
    else:
        pairs = demo_pairs()
        if not pairs:
            st.info("No demo pairs found (data/manifests/inference_manifest.json or data/fixtures).")
        else:
            name = st.selectbox("Demo pair", list(pairs))
            d = pairs[name]
            ref_path, cand_path, sample_id = d["ref"], d["cand"], d["sample_id"]
            ref_bytes, cand_bytes = ref_path.read_bytes(), cand_path.read_bytes()
            if d.get("hashes") and (
                    hashlib.sha256(ref_bytes).hexdigest() != d["hashes"]["reference"]["sha256"]
                    or hashlib.sha256(cand_bytes).hexdigest() != d["hashes"]["candidate"]["sha256"]):
                st.error("Demo input hash does not match its frozen inventory. Analysis is disabled.")
                ref_bytes = cand_bytes = None
            initial_rules = d["rules"]
            st.caption("Synthetic fixture (hand-made test image)" if name.startswith("synthetic")
                       else "Frozen development demonstration (CC BY 4.0); not a held-out test."
                       if name.startswith("Frozen dev demo") else "VideoGameQA-Bench sample (CC BY 4.0)")
        src_key = name if pairs else "none"

    st.subheader("Rules")
    rules, rules_err = rules_editor(initial_rules, src_key)
    if rules_err:
        st.error(rules_err)

    ready = ref_bytes is not None and cand_bytes is not None and rules is not None
    if mock is None and cfg_default["vlm"]["provider"] == "openai":
        key_env = cfg_default["vlm"].get("api_key_env", "OPENAI_API_KEY")
        credential = os.environ.get(key_env, "")
        if not credential or credential.startswith("mock-"):
            st.warning(f"Live analysis requires {key_env} in host secrets. Saved run replay remains available.")
            ready = False
    if ref_bytes and cand_bytes:
        s1, s2 = st.columns(2)
        s1.image(ref_bytes, caption="Reference")
        s2.image(cand_bytes, caption="Candidate")
    if st.button("Analyze", type="primary", disabled=not ready):
        key = input_hash(ref_bytes, cand_bytes, dump_rules(rules), mock)
        cached = state["runs_by_hash"].get(key)
        if cached:
            state["active_run_id"] = cached
            state["active_mode"] = "replay"
            st.info("Saved run replay — no new inference")
        else:
            cfg = make_config(mock)
            with st.status("Analyzing...", expanded=True) as status, \
                    tempfile.TemporaryDirectory() as tmp:
                st.write("Loading models" if not mock else "Preparing MOCK engine")
                extractor, judge = get_engines(config_hash(cfg), mock)
                rp, cp = Path(tmp, "reference"), Path(tmp, "candidate")
                rp.write_bytes(ref_bytes)
                cp.write_bytes(cand_bytes)
                st.write("Aligning, proposing and judging regions")
                result = pipeline.analyze(
                    PairInput(reference_path=str(rp), candidate_path=str(cp), rules=rules,
                              sample_id=sample_id), cfg, judge=judge, extractor=extractor)
                status.update(label=f"Done: {result.final_decision.value}", state="complete")
            state["runs_by_hash"][key] = result.run_id
            state["active_run_id"] = result.run_id
            state["active_mode"] = "analysis"

    active = state.get("active_run_id")
    if active:
        st.divider()
        try:
            result = load_run(active, cfg_default)
            render_result(result, run_dir_for(active, cfg_default))
        except StorageError as exc:
            st.error(f"Cannot load run {active}: {exc}")


main()
