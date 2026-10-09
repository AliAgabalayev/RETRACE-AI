"""Build an explicitly reconstructed export from immutable recorded files; no inference."""

import hashlib
import json
from pathlib import Path
import zipfile


def build(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    source = root / "deploy/replay/barrel"
    manifest_bytes = (source / "package.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    originals = {}
    for name, expected in manifest["files"].items():
        path = (source / name).resolve()
        if source.resolve() not in path.parents:
            raise RuntimeError("Invalid recorded asset path")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise RuntimeError(f"Recorded asset checksum mismatch: {name}")
        originals[name] = data
    analysis = json.loads(originals["analysis.json"])
    if analysis["run_id"] != manifest["run_id"] or analysis["sample_id"] != manifest["sample_id"]:
        raise RuntimeError("Recorded run identity mismatch")
    provenance = {
        "kind": "reconstructed_replay_export",
        "run_id": manifest["run_id"],
        "original_source_zip_sha256": manifest["source_zip_sha256"],
        "package_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "original_zip_available": False,
        "new_inference": False,
        "note": "Original run files preserved; report and evidence index reconstructed. Original ZIP unavailable.",
        "reconstructed_files": ["report.md", "evidence.json", "export-provenance.json"],
    }
    evidence = {
        "schema": "retrace-recorded-replay-export-v1",
        "run_id": analysis["run_id"],
        "sample_id": analysis["sample_id"],
        "decision": {"final": analysis["final_decision"], "reason": analysis["decision_reason"]},
        "provenance": provenance,
        "original_files": manifest["files"],
        "recorded_judgments": analysis["judgments"],
        "recorded_scene_audit": analysis["scene_audit"],
        "recorded_versions": analysis["versions"],
    }
    lines = ["# RETRACE — portable recorded replay export", "", provenance["note"], "",
             "Recorded model run — replay, no new inference.", "",
             f"Run: `{analysis['run_id']}` · Sample: `{analysis['sample_id']}`", "",
             f"**{analysis['final_decision']}**: {analysis['decision_reason']}", "",
             "## Original screenshots", "",
             "[Reference](images/reference.png) · [Candidate](images/candidate.png)", "",
             "## Recorded observations", ""]
    for judgment in analysis["judgments"]:
        rid = judgment["region_id"]
        lines.extend([f"### {rid} — {judgment['verdict']}", "", judgment["observed_change"], "",
                      f"Rules: {', '.join(judgment['rule_ids'])}", "", judgment["evidence"], "",
                      f"[Reference crop](crops/{rid}_ref.png) · [Candidate crop](crops/{rid}_cand.png)", ""])
    audit = analysis.get("scene_audit")
    if audit:
        judgment = audit["judgment"]
        lines.extend(["## Recorded whole-scene audit", "", judgment["observed_change"], "", judgment["evidence"], ""])
    lines.extend(["## Provenance", "", "Stored rules: [rules.yaml](rules.yaml). "
                  "Exact recorded model/runtime identity is preserved in analysis.json and runtime-identity.json.", "",
                  "Original source ZIP is unavailable; this archive is not byte-identical to it. "
                  "All original file hashes are listed in package.json and evidence.json.", "",
                  "VideoGameQA-Bench screenshots: CC BY 4.0. https://huggingface.co/datasets/taesiri/VideoGameQA-Bench", ""])
    entries = {**originals, "package.json": manifest_bytes,
               "report.md": "\n".join(lines).encode(),
               "evidence.json": json.dumps(evidence, indent=2, ensure_ascii=False).encode(),
               "export-provenance.json": json.dumps(provenance, indent=2).encode()}
    archive = source.parent / "barrel-replay.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(f"{manifest['run_id']}/{name}", date_time=(2026, 10, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zipped.writestr(info, data)
    descriptor = {**provenance, "archive_name": archive.name,
                  "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}
    (source.parent / "barrel-replay-export.json").write_text(json.dumps(descriptor, indent=2) + "\n")
    return archive


if __name__ == "__main__":
    print(f"Built labelled replay export: {build().name}; no new inference")
