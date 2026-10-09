"""VLM judgment (Ollama, OpenAI-compatible API, or labelled mock), strict response validation, disk cache."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import time
from pathlib import Path

import cv2
import numpy as np

from gameqa.contracts import SCENE_REGION_ID, RegionJudgment, Rule, RuleEffect, SceneAudit, Verdict
from gameqa.vision.prompts import (AUDIT_PROMPT, DECIDE_PROMPT, PROMPT_VERSION, REGION_PROMPT, STAGE1_AUDIT_SCHEMA,
                                   STAGE1_SCHEMA, STAGE2_SCHEMA)

_DISAPPEAR = re.compile(r"\b(missing|absent|gone|removed|disappear\w*|no longer|vanish\w*|deleted)\b", re.I)
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


def labelled_pair(before: np.ndarray, after: np.ndarray, max_side: int, min_h: int = 160, boxes=None, color=(255, 220, 0),
                  labels=None) -> np.ndarray:
    """ONE composite image: BEFORE (left) | AFTER (right), captions burned in. Boxes are in the frame of `before`."""
    h, w = before.shape[:2]
    s = max(min(max_side / max(h, w), 1.0 if boxes else 8.0), 0.0)
    if not boxes:  # crops: upscale small ones so the VLM can see them
        s = min(max_side / max(h, w), max(1.0, min_h / min(h, w)))
    nh, nw = max(28, round(h * s)), max(28, round(w * s))
    f = lambda im: cv2.resize(im, (nw, nh), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    a, b = f(before).copy(), f(after).copy()
    for i, bx in enumerate(boxes or []):
        _draw_box(a, bx, s, color, labels[i] if labels else None)
        _draw_box(b, bx, s, color, labels[i] if labels else None)
    fs = max(0.4, min(0.8, nh / 400))
    for im, t in ((a, "BEFORE"), (b, "AFTER")):
        cv2.putText(im, t, (4, int(18 + 6 * fs)), cv2.FONT_HERSHEY_SIMPLEX, fs, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(im, t, (4, int(18 + 6 * fs)), cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 0, 0), 1, cv2.LINE_AA)
    return np.concatenate([a, np.full((nh, 8, 3), 255, np.uint8), b], axis=1)


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


def _scene_residual(ref, cand, boxes, thr: float, min_px: int) -> tuple[int, int]:
    """(#pixels with any channel diff > 6, #pixels with blurred diff > thr outside all boxes)."""
    g1 = cv2.cvtColor(ref, cv2.COLOR_RGB2GRAY); g2 = cv2.cvtColor(cand, cv2.COLOR_RGB2GRAY)
    mad = float(np.mean(cv2.absdiff(g1, g2)))
    raw_px = int((np.abs(ref.astype(np.int16) - cand.astype(np.int16)).max(axis=2) > 6).sum())  # any visible pixel change
    d = cv2.absdiff(cv2.GaussianBlur(g1, (0, 0), 2.0), cv2.GaussianBlur(g2, (0, 0), 2.0))
    m = d > thr
    for x1, y1, x2, y2 in boxes:
        m[y1:y2, x1:x2] = False
    n = int(m.sum())
    return raw_px, (n if n >= min_px else 0)


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
    diff = data.get("any_difference", True)
    if not isinstance(diff, bool):
        errs.append("any_difference must be boolean")
        diff = True
    ctype = str(data.get("change_type", "other"))
    nvc = (not diff) and ctype in ("none", "other")
    out["no_visible_change"] = nvc
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
        if _DISAPPEAR.search(out["observed_change"] + " " + out["evidence"]) and any(r.effect is RuleEffect.DENY for r in rules):
            errs.append("allowed verdict but the text describes something missing/removed (internal contradiction)")
        if any(r.effect is RuleEffect.DENY for r in cited):
            errs.append("allowed verdict cites a deny rule (rule conflict)")
        if not cited and not nvc:
            errs.append("allowed verdict without an allow rule and not 'no difference'")
        if ctype in ("disappeared", "distorted_or_corrupted"):
            errs.append(f"allowed verdict but change_type={ctype} (never auto-allowed; needs review)")
        if cited and not diff:
            errs.append("allowed verdict cites a rule but any_difference is false")
        if not out["evidence"]:
            errs.append("allowed verdict without evidence")
    if errs:
        return out
    out["verdict"], out["validated"] = verdict, True
    return out


# ---------------- Judge ----------------
def _is_transient(exc: Exception) -> bool:
    """HTTP 429 (rate limit) / 503 (overloaded) from a hosted VLM: worth retrying after a pause."""
    text = str(exc)
    return "HTTP 429" in text or "HTTP 503" in text


class Judge:
    def __init__(self, cfg: dict):
        v = cfg.get("vlm", {})
        self.provider = v.get("provider", "ollama")
        self.base_url = v.get("base_url", "http://localhost:11434").rstrip("/")
        # Fallbacks mirror configs/default.yaml (D10); the yaml values are authoritative.
        self.timeout_s = float(v.get("timeout_s", 75))
        self.max_attempts = int(v.get("max_attempts", 2))
        self.transient_retries = int(v.get("transient_retries", 4))  # extra retries on HTTP 429/503
        self.temperature = float(v.get("temperature", 0.0))
        self.crop_max_side = int(v.get("crop_max_side", 336))
        self.context_max_side = int(v.get("context_max_side", 512))
        self.num_ctx = v.get("num_ctx", 2048)
        self.classical_thr = float(cfg.get("proposals", {}).get("classical_threshold", 40))
        self.resid_min_px = int(cfg.get("proposals", {}).get("min_area_px", 40))
        self.identical_px = int(v.get("identical_max_px", 8))
        self.use_context = bool(v.get("use_context", False))
        self.audit_max_side = int(v.get("audit_max_side", 512))
        self.keep_alive = v.get("keep_alive", "30m")
        self.warmup_timeout_s = float(v.get("warmup_timeout_s", 180))
        self.mock_behavior = v.get("mock_behavior", "uncertain")
        self.prompt_version = PROMPT_VERSION
        self.cache_enabled = bool(v.get("cache", True)) and self.provider in ("ollama", "openai")
        self.cache_dir = Path(cfg.get("run", {}).get("cache_dir", "data/cache")) / "vlm"
        self.last_cache_hit = False
        # Opt-in debug dump of exactly what each VLM request carries (unset = no behaviour change).
        d = v.get("dump_inputs_dir")
        self.dump_dir = Path(d) / str(v.get("dump_tag") or "run") if d else None
        self._cur_region = "na"
        self._dump_n: dict[tuple[str, str], int] = {}
        if self.provider == "mock":
            if self.mock_behavior not in MOCK_BEHAVIORS:
                raise ValueError(f"unknown mock_behavior {self.mock_behavior}")
            self.model_id, self.is_mock = f"mock:{self.mock_behavior}", True
        elif self.provider == "ollama":
            self.model_id, self.is_mock = f"ollama:{v.get('model', 'qwen2.5vl:3b')}", False
            self._model = v.get("model", "qwen2.5vl:3b")
        elif self.provider == "openai":
            # Any OpenAI-compatible Chat Completions endpoint (OpenAI, OpenRouter, ...). The key is
            # read from the environment variable named by vlm.api_key_env (loaded from .env).
            from gameqa.config import load_env_file
            load_env_file()
            self._model = v.get("model", "gpt-4o-mini")
            self.api_key_env = v.get("api_key_env", "OPENAI_API_KEY")
            if self.base_url.startswith("http://localhost:11434"):  # yaml default is Ollama's URL
                self.base_url = "https://api.openai.com/v1"
            host = self.base_url.split("//", 1)[-1].split("/", 1)[0]
            prefix = "openai" if host == "api.openai.com" else f"openai-compatible@{host}"
            self.model_id, self.is_mock = f"{prefix}:{self._model}", False
            self.image_detail = v.get("image_detail", "high")
            # Optional reasoning budget for "thinking" models (e.g. low/medium/high); omitted when unset.
            self.reasoning_effort = v.get("reasoning_effort")
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
        # Settings that change the answer must change the key (else a stale answer is reused).
        if getattr(self, "reasoning_effort", None):
            h.update(f"|effort={self.reasoning_effort}".encode())
        return h.hexdigest()

    def _mock_reply(self, rules: list[Rule], audit: bool) -> str:
        b = self.mock_behavior
        if b == "timeout":
            raise TimeoutError("mock timeout")
        if b == "invalid_json":
            return "Sure! The region looks different {not json"
        allow = [r.id for r in rules if r.effect is RuleEffect.ALLOW][:1]
        deny = [r.id for r in rules if r.effect is RuleEffect.DENY][:1]
        d = {"observed_change": "mock observation", "change_type": "other", "any_difference": True, "evidence": "mock evidence (no image was examined)"}
        if b == "allowed":
            d.update(verdict="allowed", rule_ids=allow)
            if not allow:
                d["observed_change"] = "no visible change (mock)"; d["change_type"] = "none"; d["any_difference"] = False
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
            "keep_alive": self.keep_alive, "options": {"temperature": self.temperature, "use_mmap": True, **({"num_ctx": self.num_ctx} if self.num_ctx else {})},
            "messages": [{"role": "user", "content": prompt, **({"images": [_png_b64(i) for i in images]} if images else {})}],
        }
        r = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout_s)
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
        return r.json()["message"]["content"]

    def _api_key(self) -> str:
        key = os.environ.get(self.api_key_env, "").strip()
        if not key or key.lower().startswith(("mock", "your-", "replace", "sk-replace")):
            raise RuntimeError(f"{self.api_key_env} is not configured (set a real key in .env); "
                               "VLM unavailable")
        return key

    def _openai_reply(self, images: list[np.ndarray], prompt: str, schema: dict) -> str:
        import httpx
        content: list[dict] = [{"type": "text", "text": prompt}]
        # "detail" is OpenAI-specific; set vlm.image_detail: null for endpoints that reject it
        img_extra = {"detail": self.image_detail} if self.image_detail else {}
        content += [{"type": "image_url",
                     "image_url": {"url": f"data:image/png;base64,{_png_b64(i)}", **img_extra}}
                    for i in images]
        payload = {
            "model": self._model, "temperature": self.temperature,
            "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "judgment", "schema": schema, "strict": False}},
        }
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        r = httpx.post(f"{self.base_url}/chat/completions", json=payload, timeout=self.timeout_s,
                       headers={"Authorization": f"Bearer {self._api_key()}"})
        if r.status_code >= 400:
            # never echo request headers; the body carries the provider's error message only
            # (800 chars keeps quota details such as quotaId/limit/retryDelay visible)
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:800]}")
        return r.json()["choices"][0]["message"]["content"]

    def _reply(self, images: list[np.ndarray], prompt: str, schema: dict) -> str:
        if self.provider == "openai":
            return self._openai_reply(images, prompt, schema)
        return self._ollama_reply(images, prompt, schema)

    def _dump_call(self, stage, images, prompt, schema, raw, errors, latency) -> None:
        """Write the exact inputs/outputs of one VLM request. Never raises, never writes keys."""
        try:
            region = re.sub(r"[^A-Za-z0-9_.-]", "_", str(self._cur_region))
            n = self._dump_n.get((region, stage), 0) + 1
            self._dump_n[(region, stage)] = n
            self.dump_dir.mkdir(parents=True, exist_ok=True)
            base = f"{region}_{stage}_{n}"
            names = []
            for k, im in enumerate(images):
                name = f"{base}.png" if k == 0 else f"{base}_{k + 1}.png"
                (self.dump_dir / name).write_bytes(base64.b64decode(_png_b64(im)))  # same bytes as sent
                names.append({"file": name, "shape_hwc": list(im.shape)})
            (self.dump_dir / f"{base}.txt").write_text(prompt)
            meta = dict(region_id=self._cur_region, stage=stage, n=n, model=self.model_id, is_mock=self.is_mock,
                        cache_hit=self.last_cache_hit, latency_s=round(latency, 3), images=names,
                        prompt_version=self.prompt_version, raw_reply=raw, errors=errors, schema=schema)
            (self.dump_dir / f"{base}.json").write_text(json.dumps(meta, indent=1))
            with (self.dump_dir / "calls.jsonl").open("a") as f:
                f.write(json.dumps({k: meta[k] for k in ("region_id", "stage", "n", "model", "is_mock", "cache_hit", "latency_s")}
                                   | {"base": base, "n_images": len(images), "ok": raw is not None}) + "\n")
        except Exception:  # noqa: BLE001
            pass

    def _ask(self, images, prompt, schema, rules, audit, stage: str = "stage1") -> tuple[str | None, list[str], float]:
        raw, errors, lat = self._ask_inner(images, prompt, schema, rules, audit)
        if self.dump_dir is not None:
            self._dump_call(stage, images, prompt, schema, raw, errors, lat)
        return raw, errors, lat

    def _ask_inner(self, images, prompt, schema, rules, audit) -> tuple[str | None, list[str], float]:
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
        transient_left = self.transient_retries
        attempt = 0
        while attempt < self.max_attempts:
            attempt += 1
            try:
                raw = self._mock_reply(rules, audit) if self.is_mock else self._reply(images, prompt, schema)
            except Exception as e:  # noqa: BLE001  (timeouts, connection, HTTP, bad payload)
                errors.append(f"provider error (attempt {attempt}): {type(e).__name__}: {e}")
                if self.is_mock:
                    continue
                # Hosted APIs return 429/503 when overloaded; that is infrastructure, not a model
                # answer, so retry with backoff without spending a regular attempt.
                if _is_transient(e) and transient_left > 0:
                    transient_left -= 1
                    attempt -= 1
                    time.sleep(min(60.0, 5.0 * 2 ** (self.transient_retries - transient_left - 1)))
                elif attempt < self.max_attempts:
                    time.sleep(3.0)
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
            # A failed earlier attempt followed by a usable answer is not a judgment error
            # (QA-D10): returning the retry notes would turn a valid answer into review.
            return raw, [], time.time() - t0
        return None, errors, time.time() - t0

    def _two_stage(self, images, stage1_prompt, audit, rules, where):
        """Stage 1 (image, no rules) then stage 2 (text only, rules). Returns (merged_raw_json|None, errors, latency).
        Mock provider: single call returning the final JSON."""
        s1 = "audit" if audit else "stage1"
        if self.is_mock:
            return self._ask(images, stage1_prompt, STAGE1_AUDIT_SCHEMA if audit else STAGE1_SCHEMA, rules, audit, s1)
        raw1, e1, l1 = self._ask(images, stage1_prompt, STAGE1_AUDIT_SCHEMA if audit else STAGE1_SCHEMA, rules, audit, s1)
        if raw1 is None:
            return None, e1, l1
        try:
            d1 = json.loads(raw1)
            assert isinstance(d1, dict)
        except Exception as e:  # noqa: BLE001
            return raw1, e1 + [f"stage1 not a JSON object: {e}"], l1
        f = self._rule_fields(rules)
        p2 = DECIDE_PROMPT.format(where=where, before_shows=d1.get("before_shows", ""), after_shows=d1.get("after_shows", ""),
                                  observed_change=d1.get("observed_change", ""), change_type=d1.get("change_type", ""),
                                  any_difference=str(d1.get("any_difference", "")).lower(),
                                  rules=f["rules"], allow_ids=f["allow_ids"], deny_ids=f["deny_ids"])
        raw2, e2, l2 = self._ask([], p2, STAGE2_SCHEMA, rules, False, "audit_stage2" if audit else "stage2")
        if raw2 is None:
            return None, e1 + e2, l1 + l2
        try:
            d2 = json.loads(raw2)
            assert isinstance(d2, dict)
        except Exception as e:  # noqa: BLE001
            return raw2, e1 + e2 + [f"stage2 not a JSON object: {e}"], l1 + l2
        return json.dumps({**d1, **d2}), e1 + e2, l1 + l2

    def _to_judgment(self, region_id, raw, perr, latency, rules, audit):
        if raw is None:
            return RegionJudgment(region_id=region_id, observed_change="", verdict=Verdict.UNCERTAIN, model=self.model_id,
                                  is_mock=self.is_mock, errors=perr or ["no response"], validated=False, latency_s=latency), False
        p = validate_response(raw, rules, audit)
        return RegionJudgment(region_id=region_id, observed_change=p["observed_change"], verdict=p["verdict"],
                              rule_ids=p["rule_ids"], evidence=p["evidence"],
                              model=self.model_id, is_mock=self.is_mock, errors=perr + p["errors"],
                              validated=p["validated"], latency_s=latency), p["extra"]

    @staticmethod
    def _rule_fields(rules: list[Rule]) -> dict:
        allow = [r.id for r in rules if r.effect is RuleEffect.ALLOW]
        deny = [r.id for r in rules if r.effect is RuleEffect.DENY]
        return dict(rules="\n".join(f"- {r.id} [{r.effect.value.upper()}]: {r.description}" for r in rules),
                    allow_ids=", ".join(allow) or "(none)", deny_ids=", ".join(deny) or "(none)")

    def warmup(self) -> dict:
        """Load the model into memory (cold load can take ~70 s on CPU). Never raises."""
        if self.is_mock:
            return {"ok": True, "mock": True, "seconds": 0.0}
        if self.provider == "openai":  # hosted model: nothing to load; only check the key exists
            try:
                self._api_key()
                return {"ok": True, "seconds": 0.0}
            except RuntimeError as e:
                return {"ok": False, "seconds": 0.0, "error": str(e)}
        import httpx
        t0 = time.time()
        try:
            r = httpx.post(f"{self.base_url}/api/chat", timeout=self.warmup_timeout_s, json={
                "model": self._model, "stream": False, "keep_alive": self.keep_alive,
                "options": {"num_ctx": self.num_ctx, "num_predict": 1, "use_mmap": True},
                "messages": [{"role": "user", "content": "ok"}]})
            return {"ok": r.status_code < 400, "seconds": time.time() - t0, "status": r.status_code}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "seconds": time.time() - t0, "error": f"{type(e).__name__}: {e}"}

    # ---- public API ----
    def judge_region(self, proposal, ref_crop, cand_crop, ref_context, cand_context, rules) -> RegionJudgment:
        try:
            self._cur_region = proposal.id
            x1, y1, x2, y2 = proposal.box
            prompt = REGION_PROMPT.format(x1=x1, y1=y1, x2=x2, y2=y2)
            imgs = [labelled_pair(ref_crop, cand_crop, self.crop_max_side)]
            if self.use_context:
                imgs.append(side_by_side(ref_context, cand_context, [proposal.box], self.context_max_side))
            raw, perr, lat = self._two_stage(imgs, prompt, False, rules, f" (region [{x1},{y1},{x2},{y2}])")
            j, _ = self._to_judgment(proposal.id, raw, perr, lat, rules, False)
            return j
        except Exception as e:  # noqa: BLE001
            return RegionJudgment(region_id=proposal.id, observed_change="", verdict=Verdict.UNCERTAIN, model=self.model_id,
                                  is_mock=self.is_mock, errors=[f"judge_region failure: {type(e).__name__}: {e}"], validated=False)

    def audit_scene(self, reference, aligned_candidate, rules, proposals) -> SceneAudit:
        try:
            self._cur_region = SCENE_REGION_ID
            boxes = [p.box for p in proposals]
            btxt = ", ".join(f"{p.id}={list(p.box)}" for p in proposals) or "none"
            prompt = AUDIT_PROMPT.format(boxes=btxt)
            comp = labelled_pair(reference, aligned_candidate, self.audit_max_side, boxes=boxes, labels=[p.id for p in proposals])
            diff_px, resid = _scene_residual(reference, aligned_candidate, boxes, self.classical_thr, self.resid_min_px)
            if not proposals and diff_px <= self.identical_px and resid == 0:
                # Documented deterministic shortcut: pixel-identical pair, nothing to audit. NOT a VLM result.
                return SceneAudit(judgment=RegionJudgment(
                    region_id=SCENE_REGION_ID, observed_change="no visible change", verdict=Verdict.ALLOWED, rule_ids=[],
                    evidence=f"pixel-identical within tolerance ({diff_px} px differ by more than 6 levels)",
                    model="deterministic:pixel-identical", is_mock=False, errors=[], validated=True, latency_s=0.0),
                    extra_changes_reported=False)
            raw, perr, lat = self._two_stage([comp], prompt, True, rules, " (whole scene)")
            j, extra = self._to_judgment(SCENE_REGION_ID, raw, perr, lat, rules, True)
            if j.validated and j.verdict is Verdict.FORBIDDEN and resid == 0:
                # A 3B VLM hallucinates 'forbidden' on near-identical pairs (measured). A scene-level forbidden claim
                # needs pixel support OUTSIDE the already-judged boxes; otherwise it is not trusted.
                j = j.model_copy(update={"verdict": Verdict.UNCERTAIN, "validated": False,
                    "errors": j.errors + ["audit forbidden claim has no pixel evidence outside proposed regions; downgraded to uncertain"]})
            # if the audit could not be validated we cannot claim it found nothing extra
            return SceneAudit(judgment=j, extra_changes_reported=bool(extra) if j.validated else False)
        except Exception as e:  # noqa: BLE001
            j = RegionJudgment(region_id=SCENE_REGION_ID, observed_change="", verdict=Verdict.UNCERTAIN, model=self.model_id,
                               is_mock=self.is_mock, errors=[f"audit_scene failure: {type(e).__name__}: {e}"], validated=False)
            return SceneAudit(judgment=j, extra_changes_reported=False)
