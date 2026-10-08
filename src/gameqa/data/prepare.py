"""Download, verify and manifest VideoGameQA-Bench visual-regression pairs.

Only selected files are fetched (never the whole repository).
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pandas as pd
from PIL import Image

from gameqa.data.manifest import REPO_ROOT, rules_from_question

REPO_ID = "taesiri/VideoGameQA-Bench"
PARQUET_PATH = "data/test-00000-of-00001.parquet"
CATEGORY = "VisualRegression"
IMAGE_NAMES = ("question_images_0.jpg", "question_images_1.jpg")  # (reference, candidate)
SEED = 13
DEMO_MAX = 5
DEV_FRACTION = 0.15

DATA = REPO_ROOT / "data"
RAW_META = DATA / "raw" / "metadata"
RAW_IMAGES = DATA / "raw" / "images"
WORK = DATA / "work"
MANIFESTS = DATA / "manifests"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_revision(revision: str | None = None) -> str:
    from huggingface_hub import HfApi

    return HfApi().dataset_info(REPO_ID, revision=revision).sha


def download_metadata(revision: str) -> pd.DataFrame:
    from huggingface_hub import hf_hub_download

    p = hf_hub_download(REPO_ID, PARQUET_PATH, repo_type="dataset", revision=revision, local_dir=RAW_META)
    return pd.read_parquet(p)


def select_visual_regression(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["question_categories"].apply(lambda c: CATEGORY in list(c))
    return df[mask].reset_index(drop=True)


def parse_label(ground_truth_raw: str) -> str | None:
    """'{"test_pass": false}' -> 'bug'; '{"test_pass": true}' -> 'no_bug'; anything else -> None."""
    try:
        v = json.loads(ground_truth_raw).get("test_pass")
    except (ValueError, AttributeError):
        return None
    if v is False:
        return "bug"
    if v is True:
        return "no_bug"
    return None


def sample_id_for(custom_id: str) -> str:
    return f"vr_{custom_id[:8]}"


def ordered_records(vr: pd.DataFrame, seed: int = SEED) -> list[dict]:
    """Seeded order where every 4th record is no_bug, so any prefix (--limit N) has both classes."""
    recs = vr.to_dict("records")
    rng = random.Random(seed)
    bug = [r for r in recs if parse_label(r["ground_truth"]) != "no_bug"]
    ok = [r for r in recs if parse_label(r["ground_truth"]) == "no_bug"]
    rng.shuffle(bug)
    rng.shuffle(ok)
    out: list[dict] = []
    while bug or ok:
        for _ in range(3):
            if bug:
                out.append(bug.pop())
        if ok:
            out.append(ok.pop())
    return out


def remote_paths(custom_id: str) -> list[str]:
    return [f"images/{custom_id}/{n}" for n in IMAGE_NAMES]


def remote_sizes(custom_ids: list[str], revision: str) -> dict[str, int]:
    from huggingface_hub import HfApi

    paths = [p for c in custom_ids for p in remote_paths(c)]
    out: dict[str, int] = {}
    api = HfApi()
    for i in range(0, len(paths), 200):
        for info in api.get_paths_info(REPO_ID, paths[i : i + 200], repo_type="dataset", revision=revision):
            out[info.path] = info.size
    return out


def _fetch(remote: str, revision: str) -> Path:
    from huggingface_hub import hf_hub_download

    return Path(hf_hub_download(REPO_ID, remote, repo_type="dataset", revision=revision, local_dir=RAW_IMAGES.parent / "hf"))


def prepare_pair(rec: dict, revision: str) -> dict:
    """Download + decode + hash one pair and write data/work/<sample_id>/{reference,candidate}.png.

    Returns a partial manifest record with validation_status 'ok' or 'failed: <reason>'.
    """
    cid = rec["custom_id"]
    sid = sample_id_for(cid)
    out: dict = {"sample_id": sid, "custom_id": cid, "validation_status": "ok"}
    try:
        for role, name, remote in zip(("reference", "candidate"), IMAGE_NAMES, remote_paths(cid)):
            raw = RAW_IMAGES / cid / name
            if not raw.exists():
                src = _fetch(remote, revision)
                raw.parent.mkdir(parents=True, exist_ok=True)
                src.replace(raw)
            sha = sha256_file(raw)
            with Image.open(raw) as im:
                im.load()
                rgb = im.convert("RGB")
            work = WORK / sid / f"{role}.png"
            work.parent.mkdir(parents=True, exist_ok=True)
            if not work.exists():
                rgb.save(work, format="PNG")
            out[f"{role}_path"] = work.relative_to(REPO_ROOT).as_posix()
            out[f"{role}_raw_path"] = raw.relative_to(REPO_ROOT).as_posix()
            out[f"sha256_{role}"] = sha
            out[f"{role}_width"], out[f"{role}_height"] = rgb.size
    except Exception as e:  # noqa: BLE001 - record any download/decode failure per sample
        out["validation_status"] = f"failed: {type(e).__name__}: {e}"
    return out


def _group_ids(prepared: list[dict]) -> dict[str, str]:
    """Union samples that share any image sha256 (reference or candidate)."""
    parent = {p["sample_id"]: p["sample_id"] for p in prepared}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner: dict[str, str] = {}
    for p in prepared:
        for k in ("sha256_reference", "sha256_candidate"):
            s = p[k]
            if s in owner:
                parent[find(p["sample_id"])] = find(owner[s])
            else:
                owner[s] = p["sample_id"]
    roots: dict[str, list[str]] = {}
    for sid in parent:
        roots.setdefault(find(sid), []).append(sid)
    return {sid: "g_" + min(members) for members in roots.values() for sid in members}


def assign_splits(items: list[dict], seed: int = SEED) -> dict[str, str]:
    """items: [{sample_id, group_id, label}]. Labels are used ONLY to balance demo and stratify dev."""
    rng = random.Random(seed)
    groups: dict[str, list[dict]] = {}
    for it in items:
        groups.setdefault(it["group_id"], []).append(it)
    split: dict[str, str] = {}
    gids = sorted(groups)
    rng.shuffle(gids)
    # demo: up to 5 singleton-or-small groups, 3 bug + 2 no_bug when available
    want = {"bug": 3, "no_bug": 2}
    demo_ids: list[str] = []
    for g in gids:
        members = groups[g]
        labs = {m["label"] for m in members}
        if len(demo_ids) + len(members) > DEMO_MAX or len(members) != 1:
            continue
        lab = next(iter(labs))
        if want.get(lab, 0) > 0:
            want[lab] -= 1
            demo_ids.append(g)
    for g in demo_ids:
        for m in groups[g]:
            split[m["sample_id"]] = "demo"
    rest = [g for g in gids if g not in demo_ids]
    n_rest = sum(len(groups[g]) for g in rest)
    target_dev = round(DEV_FRACTION * n_rest) if n_rest >= 7 else 0
    with_ok = [g for g in rest if any(m["label"] == "no_bug" for m in groups[g])]
    without = [g for g in rest if g not in with_ok]
    dev_count = 0
    dev_groups: set[str] = set()
    for pool_frac in (with_ok, without):
        quota = round(target_dev * sum(len(groups[g]) for g in pool_frac) / max(n_rest, 1))
        c = 0
        for g in pool_frac:
            if c >= quota:
                break
            dev_groups.add(g)
            c += len(groups[g])
        dev_count += c
    for g in rest:
        for m in groups[g]:
            split[m["sample_id"]] = "dev" if g in dev_groups else "eval"
    return split


def build_manifests(selected: list[dict], prepared: list[dict], revision: str) -> dict:
    by_cid = {r["custom_id"]: r for r in selected}
    ok = [p for p in prepared if p["validation_status"] == "ok"]
    groups = _group_ids(ok)
    items = [
        {"sample_id": p["sample_id"], "group_id": groups[p["sample_id"]], "label": parse_label(by_cid[p["custom_id"]]["ground_truth"])}
        for p in ok
    ]
    split = assign_splits(items)
    inference, labels = [], {}
    for p in prepared:
        rec = by_cid[p["custom_id"]]
        sid = p["sample_id"]
        sp = split.get(sid)
        inference.append(
            {
                "sample_id": sid,
                "custom_id": p["custom_id"],
                "reference_path": p.get("reference_path"),
                "candidate_path": p.get("candidate_path"),
                "reference_raw_path": p.get("reference_raw_path"),
                "candidate_raw_path": p.get("candidate_raw_path"),
                "rules": [r.model_dump(mode="json") for r in rules_from_question(rec["question"])],
                "question": rec["question"],
                "split": sp,
                "group_id": groups.get(sid),
                "media_source": rec["media_source"],
                "dataset_revision": revision,
                "sha256_reference": p.get("sha256_reference"),
                "sha256_candidate": p.get("sha256_candidate"),
                "reference_width": p.get("reference_width"),
                "reference_height": p.get("reference_height"),
                "candidate_width": p.get("candidate_width"),
                "candidate_height": p.get("candidate_height"),
                "validation_status": p["validation_status"],
            }
        )
        labels[sid] = {"ground_truth_raw": rec["ground_truth"], "label": parse_label(rec["ground_truth"]), "split": sp}
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    (MANIFESTS / "inference_manifest.json").write_text(json.dumps(inference, indent=2), encoding="utf-8")
    (MANIFESTS / "eval_labels.json").write_text(json.dumps(labels, indent=2), encoding="utf-8")
    return {
        "revision": revision,
        "n": len(prepared),
        "ok": len(ok),
        "failed": len(prepared) - len(ok),
        "split_label_counts": {f"{s}/{l}": n for (s, l), n in sorted(Counter((v["split"], v["label"]) for v in labels.values()).items(), key=str)},
    }
