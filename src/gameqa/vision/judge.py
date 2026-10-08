"""VLM judgment (Ollama or labelled mock), strict response validation, disk cache."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import time
from pathlib import Path

import cv2
import numpy as np

from gameqa.contracts import RegionJudgment, Rule, RuleEffect, SceneAudit, Verdict
from gameqa.vision.prompts import AUDIT_PROMPT, AUDIT_SCHEMA, PROMPT_VERSION, REGION_PROMPT, REGION_SCHEMA

_NO_CHANGE = re.compile(r"\b(no (visible |noticeable |significant )?(change|difference)s?|identical|unchanged|same)\b", re.I)
MOCK_BEHAVIORS = ("allowed", "forbidden", "uncertain", "timeout", "invalid_json", "unknown_rule")


# ---------------- image helpers ----------------
def _png_b64(img: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    if not ok:
        raise ValueError("png encode failed")
    return base64.b64encode(buf.tobytes()).decode()


def _fit(img: np.ndarray, max_side: int) -> tuple[np.ndarray, float]:
    h, w = img.shape[:2]
    s = min(1.0, max_side / max(h, w))
    if s == 1.0:
        return img, 1.0
    return cv2.resize(img, (max(1, round(w * s)), max(1, round(h * s))), interpolation=cv2.INTER_AREA), s


def _draw_box(img: np.ndarray, box, scale: float, color, label: str | None = None) -> None:
    x1, y1, x2, y2 = [int(round(v * scale)) for v in box]
    t = max(2, int(round(min(img.shape[:2]) / 200)))
    cv2.rectangle(img, (x1, y1), (max(x1 + 1, x2 - 1), max(y1 + 1, y2 - 1)), color, t)
    if label:
        cv2.putText(img, label, (x1 + 2, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)


def side_by_side(ref: np.ndarray, cand: np.ndarray, boxes, half_max_side: int, color=(255, 0, 0), labels=None) -> np.ndarray:
    """Left = REFERENCE, right = CANDIDATE, boxes (reference coords) drawn on both."""
    a, s = _fit(ref, half_max_side)
    b, _ = _fit(cand, half_max_side)
    if b.shape != a.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]))
    a, b = a.copy(), b.copy()
    for i, bx in enumerate(boxes):
        lab = labels[i] if labels else None
        _draw_box(a, bx, s, color, lab)
        _draw_box(b, bx, s, color, lab)
    gap = np.full((a.shape[0], 6, 3), 255, np.uint8)
    return np.concatenate([a, gap, b], axis=1)


# ---------------- validation ----------------
def validate_response(raw: str, rules: list[Rule], audit: bool = False) -> dict:
    """Parse + validate a raw model reply. Returns dict(verdict, observed_change, rule_ids, evidence,
    extra, errors, validated). On any problem verdict is forced to 'uncertain' and validated=False."""
    out = dict(verdict=Verdict.UNCERTAIN, observed_change="", rule_ids=[], evidence="", extra=False,
               errors=[], validated=False)
    errs = out["errors"]
    txt = raw.strip()
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", txt, re.S)
    if m:
        txt = m.group(1)
    try:
        data = json.loads(txt)
    except Exception as e:  # noqa: BLE001
        errs.append(f"malformed JSON: {e}")
        return out
    if not isinstance(data, dict):
        errs.append("response is not a JSON object")
        return out
    need = ["observed_change", "verdict", "rule_ids", "evidence"] + (["other_changes_outside_boxes"] if audit else [])
    missing = [k for k in need if k not in data]
    if missing:
        errs.append(f"missing keys: {missing}")
    oc, ev, ids = data.get("observed_change", ""), data.get("evidence", ""), data.get("rule_ids", [])
    if not isinstance(oc, str) or not isinstance(ev, str):
        errs.append("observed_change/evidence must be strings")
        oc, ev = str(oc), str(ev)
    out["observed_change"], out["evidence"] = oc.strip(), ev.strip()
    if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
        errs.append("rule_ids must be a list of strings")
        ids = []
    out["rule_ids"] = ids
    if audit:
        v = data.get("other_changes_outside_boxes")
        if isinstance(v, bool):
            out["extra"] = v
        elif "other_changes_outside_boxes" in data:
            errs.append("other_changes_outside_boxes must be boolean")
    try:
        verdict = Verdict(str(data.get("verdict", "")).lower())
    except ValueError:
        errs.append(f"invalid verdict {data.get('verdict')!r}")
        return out
    by_id = {r.id: r for r in rules}
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        errs.append(f"unknown rule ids: {unknown}")
    if errs:
        return out
    cited = [by_id[i] for i in ids]
    if verdict is Verdict.FORBIDDEN:
        if not any(r.effect is RuleEffect.DENY for r in cited):
            errs.append("forbidden verdict must cite a deny rule")
        if any(r.effect is RuleEffect.ALLOW for r in cited):
            errs.append("forbidden verdict cites an allow rule (rule conflict)")
        if not out["evidence"]:
            errs.append("forbidden verdict without evidence")
    elif verdict is Verdict.ALLOWED:
        if any(r.effect is RuleEffect.DENY for r in cited):
            errs.append("allowed verdict cites a deny rule (rule conflict)")
        if not cited and not _NO_CHANGE.search(out["observed_change"]):
            errs.append("allowed verdict without an allow rule and not 'no visible change'")
        if not out["evidence"]:
            errs.append("allowed verdict without evidence")
    if errs:
        return out
    out["verdict"], out["validated"] = verdict, True
    return out


# ---------------- Judge ----------------
class Judge:
    def __init__(self, cfg: dict):
        v = cfg.get("vlm", {})
        self.provider = v.get("provider", "ollama")
        self.base_url = v.get("base_url", "http://localhost:11434").rstrip("/")
        self.timeout_s = float(v.get("timeout_s", 30))
        self.max_attempts = int(v.get("max_attempts", 2))
        self.temperature = float(v.get("temperature", 0.0))
        self.crop_max_side = int(v.get("crop_max_side", 448))
        self.context_max_side = int(v.get("context_max_side", 768))
        self.num_ctx = v.get("num_ctx")
        self.mock_behavior = v.get("mock_behavior", "uncertain")
        self.prompt_version = PROMPT_VERSION
        self.cache_enabled = bool(v.get("cache", True)) and self.provider == "ollama"
        self.cache_dir = Path(cfg.get("run", {}).get("cache_dir", "data/cache")) / "vlm"
        self.last_cache_hit = False
        if self.provider == "mock":
            if self.mock_behavior not in MOCK_BEHAVIORS:
                raise ValueError(f"unknown mock_behavior {self.mock_behavior}")
            self.model_id, self.is_mock = f"mock:{self.mock_behavior}", True
        elif self.provider == "ollama":
            self.model_id, self.is_mock = f"ollama:{v.get('model', 'qwen2.5vl:3b')}", False
            self._model = v.get("model", "qwen2.5vl:3b")
        else:
            raise ValueError(f"unknown vlm provider {self.provider}")

    # ---- provider layer ----
    def _cache_key(self, images: list[np.ndarray], prompt: str, schema: dict) -> str:
        h = hashlib.sha256()
        for im in images:
            h.update(str(im.shape).encode())
            h.update(np.ascontiguousarray(im).tobytes())
        h.update(prompt.encode())
        h.update(json.dumps(schema, sort_keys=True).encode())
        h.update(f"{self.model_id}|{self.prompt_version}|{self.temperature}|{self.num_ctx}".encode())
        return h.hexdigest()

    def _mock_reply(self, rules: list[Rule], audit: bool) -> str:
        b = self.mock_behavior
        if b == "timeout":
            raise TimeoutError("mock timeout")
        if b == "invalid_json":
            return "Sure! The region looks different {not json"
        allow = [r.id for r in rules if r.effect is RuleEffect.ALLOW][:1]
        deny = [r.id for r in rules if r.effect is RuleEffect.DENY][:1]
        d = {"observed_change": "mock observation", "evidence": "mock evidence (no image was examined)"}
        if b == "allowed":
            d.update(verdict="allowed", rule_ids=allow)
            if not allow:
                d["observed_change"] = "no visible change (mock)"
        elif b == "forbidden":
            d.update(verdict="forbidden", rule_ids=deny)
        elif b == "unknown_rule":
            d.update(verdict="forbidden", rule_ids=["Z99"])
        else:
            d.update(verdict="uncertain", rule_ids=[])
        if audit:
            d["other_changes_outside_boxes"] = False
        return json.dumps(d)

    def _ollama_reply(self, images: list[np.ndarray], prompt: str, schema: dict) -> str:
        import httpx
        payload = {
            "model": self._model, "stream": False, "format": schema,
            "options": {"temperature": self.temperature, **({"num_ctx": self.num_ctx} if self.num_ctx else {})},
            "messages": [{"role": "user", "content": prompt, "images": [_png_b64(i) for i in images]}],
        }
        r = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()["message"]["content"]

    def _ask(self, images, prompt, schema, rules, audit) -> tuple[str | None, list[str], float]:
        """Returns (raw_text|None, errors, latency). Never raises."""
        self.last_cache_hit = False
        t0 = time.time()
        key = None
        if self.cache_enabled:
            key = self._cache_key(images, prompt, schema)
            f = self.cache_dir / f"{key}.json"
            try:
                if f.exists():
                    self.last_cache_hit = True
                    return json.loads(f.read_text())["raw"], [], 0.0
            except Exception:  # noqa: BLE001
                pass
        errors: list[str] = []
        for attempt in range(1, self.max_attempts + 1):
            try:
                raw = self._mock_reply(rules, audit) if self.is_mock else self._ollama_reply(images, prompt, schema)
            except Exception as e:  # noqa: BLE001  (timeouts, connection, HTTP, bad payload)
                errors.append(f"provider error (attempt {attempt}): {type(e).__name__}: {e}")
                continue
            parsed = validate_response(raw, rules, audit)
            # retry only on unparsable output; a parsed-but-inconsistent reply is returned as is
            if any(x.startswith("malformed JSON") for x in parsed["errors"]) and attempt < self.max_attempts:
                errors.append(f"attempt {attempt}: malformed JSON, retrying")
                continue
            if key and not any(x.startswith("malformed JSON") for x in parsed["errors"]):
                try:
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                    (self.cache_dir / f"{key}.json").write_text(json.dumps({"raw": raw, "model": self.model_id, "prompt_version": self.prompt_version}))
                except OSError:
                    pass
            return raw, errors, time.time() - t0
        return None, errors, time.time() - t0

    def _to_judgment(self, region_id, raw, perr, latency, rules, audit):
        if raw is None:
            return RegionJudgment(region_id=region_id, observed_change="", verdict=Verdict.UNCERTAIN, model=self.model_id,
                                  is_mock=self.is_mock, errors=perr or ["no response"], validated=False, latency_s=latency), False
        p = validate_response(raw, rules, audit)
        return RegionJudgment(region_id=region_id, observed_change=p["observed_change"], verdict=p["verdict"],
                              rule_ids=p["rule_ids"] if p["validated"] else p["rule_ids"], evidence=p["evidence"],
                              model=self.model_id, is_mock=self.is_mock, errors=perr + p["errors"],
                              validated=p["validated"], latency_s=latency), p["extra"]

    @staticmethod
    def _rules_text(rules: list[Rule]) -> str:
        return "\n".join(f"- {r.id} [{r.effect.value.upper()}]: {r.description}" for r in rules)

    # ---- public API ----
    def judge_region(self, proposal, ref_crop, cand_crop, ref_context, cand_context, rules) -> RegionJudgment:
        try:
            x1, y1, x2, y2 = proposal.box
            prompt = REGION_PROMPT.format(x1=x1, y1=y1, x2=x2, y2=y2, rules=self._rules_text(rules))
            a, _ = _fit(ref_crop, self.crop_max_side)
            b, _ = _fit(cand_crop, self.crop_max_side)
            ctx = side_by_side(ref_context, cand_context, [proposal.box], self.context_max_side)
            raw, perr, lat = self._ask([a, b, ctx], prompt, REGION_SCHEMA, rules, False)
            j, _ = self._to_judgment(proposal.id, raw, perr, lat, rules, False)
            return j
        except Exception as e:  # noqa: BLE001
            return RegionJudgment(region_id=proposal.id, observed_change="", verdict=Verdict.UNCERTAIN, model=self.model_id,
                                  is_mock=self.is_mock, errors=[f"judge_region failure: {type(e).__name__}: {e}"], validated=False)

    def audit_scene(self, reference, aligned_candidate, rules, proposals) -> SceneAudit:
        try:
            boxes = [p.box for p in proposals]
            btxt = ", ".join(f"{p.id}={list(p.box)}" for p in proposals) or "none"
            prompt = AUDIT_PROMPT.format(boxes=btxt, rules=self._rules_text(rules))
            a, s = _fit(reference, self.context_max_side)
            b, _ = _fit(aligned_candidate, self.context_max_side)
            a, b = a.copy(), b.copy()
            for p in proposals:
                _draw_box(a, p.box, s, (255, 220, 0), p.id)
                _draw_box(b, p.box, s, (255, 220, 0), p.id)
            raw, perr, lat = self._ask([a, b], prompt, AUDIT_SCHEMA, rules, True)
            j, extra = self._to_judgment("SCENE", raw, perr, lat, rules, True)
            # if the audit could not be validated we cannot claim it found nothing extra
            return SceneAudit(judgment=j, extra_changes_reported=bool(extra) if j.validated else False)
        except Exception as e:  # noqa: BLE001
            j = RegionJudgment(region_id="SCENE", observed_change="", verdict=Verdict.UNCERTAIN, model=self.model_id,
                               is_mock=self.is_mock, errors=[f"audit_scene failure: {type(e).__name__}: {e}"], validated=False)
            return SceneAudit(judgment=j, extra_changes_reported=False)
