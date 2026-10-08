"""Markdown bug-report rendering and box drawing helpers."""

from __future__ import annotations

import cv2
import numpy as np

from gameqa.contracts import AnalysisResult, RegionProposal

_COLOR = (255, 64, 64)


def draw_boxes(
    image: np.ndarray,
    proposals: list[RegionProposal],
    candidate_to_reference: list[list[float]] | None = None,
) -> np.ndarray:
    """Draw numbered boxes. Boxes are in reference coordinates; if a candidate->reference
    transform is given they are mapped back into the original candidate frame."""
    out = np.ascontiguousarray(image.copy())
    inv = None
    if candidate_to_reference is not None:
        try:
            inv = np.linalg.inv(np.asarray(candidate_to_reference, dtype=np.float64))
        except np.linalg.LinAlgError:
            inv = None
    thick = max(2, round(max(out.shape[:2]) / 400))
    for p in proposals:
        x1, y1, x2, y2 = p.box
        corners = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.float64)
        if inv is not None:
            h = np.hstack([corners, np.ones((4, 1))]) @ inv.T
            corners = h[:, :2] / h[:, 2:3]
        pts = np.round(corners).astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(out, [pts], True, _COLOR, thick)
        tx, ty = int(pts[0, 0, 0]), int(pts[0, 0, 1])
        scale = max(0.5, max(out.shape[:2]) / 1200)
        cv2.putText(out, p.id, (tx + 2, max(ty - 4, 12)), cv2.FONT_HERSHEY_SIMPLEX, scale, _COLOR, thick)
    return out


def _rules_block(result: AnalysisResult) -> list[str]:
    if not result.rules:
        return ["_No rules were provided._"]
    return [f"- **{r.id}** ({r.effect.value}): {r.description}" for r in result.rules]


def render_report(result: AnalysisResult) -> str:
    sample = result.sample_id or "n/a"
    lines = [
        f"# Visual regression report: {result.final_decision.value}",
        "",
        f"- Run ID: `{result.run_id}`",
        f"- Sample ID: `{sample}`",
        f"- Created (UTC): {result.created_at}",
        f"- Engine mode: **{result.engine_mode}**"
        + (" (MOCK: not real model inference)" if result.engine_mode == "mock" else ""),
        f"- Execution status: {result.execution_status.value}",
        "",
        "This is an automated screenshot comparison report. It carries no engine/build "
        "metadata and no gameplay reproduction steps; those need human follow-up.",
        "",
        "## Decision",
        "",
        f"**{result.final_decision.value}**: {result.decision_reason}",
        "",
        "## Expected behavior (rules)",
        "",
        *_rules_block(result),
        "",
        "## Observed behavior",
        "",
        "Reference: `images/reference.png`; candidate: `images/candidate.png`; "
        "aligned candidate: `images/aligned_candidate.png`; overlay: `images/overlay.png`.",
        "",
    ]
    if result.judgments:
        for j in result.judgments:
            prop = next((p for p in result.proposals if p.id == j.region_id), None)
            box = f" box={list(prop.box)}" if prop else ""
            lines += [
                f"### {j.region_id} ({j.verdict.value}){box}",
                "",
                f"- Observed change: {j.observed_change or 'n/a'}",
                f"- Applicable rules: {', '.join(j.rule_ids) or 'none cited'}",
                f"- Evidence: {j.evidence or 'n/a'}",
                f"- Model: {j.model}{' (MOCK)' if j.is_mock else ''}; validated: {j.validated}",
            ]
            if j.errors:
                lines.append(f"- Errors: {'; '.join(j.errors)}")
            lines += [
                "",
                f"![{j.region_id} reference](crops/{j.region_id}_ref.png) "
                f"![{j.region_id} candidate](crops/{j.region_id}_cand.png)",
                "",
            ]
    else:
        lines += ["_No regions were judged._", ""]
    if result.scene_audit:
        a = result.scene_audit
        lines += [
            "## Whole-scene audit",
            "",
            f"- Verdict: {a.judgment.verdict.value}",
            f"- Observed: {a.judgment.observed_change or 'n/a'}",
            f"- Rules: {', '.join(a.judgment.rule_ids) or 'none'}",
            f"- Evidence: {a.judgment.evidence or 'n/a'}",
            f"- Extra changes reported outside proposals: {a.extra_changes_reported}",
            f"- Model: {a.judgment.model}{' (MOCK)' if a.judgment.is_mock else ''}",
            "",
        ]
    c = result.coverage
    v = result.versions
    lines += [
        "## Coverage",
        "",
        f"- Proposals judged: {c.proposals_judged}/{c.proposals_total}; truncated: {c.truncated}; "
        f"scene audit ran: {c.scene_audit_ran}; deadline exceeded: {c.deadline_exceeded}",
        f"- Alignment: {result.alignment.status.value if result.alignment else 'n/a'}",
        "",
        "## Versions",
        "",
        f"- Feature model: {v.feature_model}",
        f"- VLM: {v.vlm_model} (prompt {v.prompt_version})",
        f"- Config hash: {v.config_hash}",
        f"- Device/dtype: {v.device}/{v.dtype}",
        "",
        "## Timings (s)",
        "",
        *[f"- {k}: {t:.2f}" for k, t in result.timings.items()],
        "",
    ]
    if result.errors:
        lines += ["## Pipeline errors", "", *[f"- {e}" for e in result.errors], ""]
    return "\n".join(lines)
