"""OpenAI-compatible VLM provider: request shape, key handling, error-to-review (no network)."""

import json

import numpy as np
import pytest

from gameqa.config import load_config
from gameqa.contracts import RegionProposal, Rule, Verdict
from gameqa.vision.judge import Judge

RULES = [Rule(id="A1", effect="allow", description="lighting may change"),
         Rule(id="D1", effect="deny", description="objects must not disappear")]


def _cfg(**vlm):
    return {"vlm": {"provider": "openai", "model": "gpt-4o-mini", "max_attempts": 1, "cache": False, **vlm}}


class _Resp:
    def __init__(self, status, body):
        self.status_code, self._body, self.text = status, body, json.dumps(body)

    def json(self):
        return self._body


def test_model_id_and_default_endpoint(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    j = Judge(_cfg())
    assert j.model_id == "openai:gpt-4o-mini" and not j.is_mock
    assert j.base_url == "https://api.openai.com/v1"
    r = Judge(_cfg(base_url="https://openrouter.ai/api/v1", model="openai/gpt-4o-mini",
                   api_key_env="OPENROUTER_API_KEY"))
    assert r.model_id == "openai-compatible@openrouter.ai:openai/gpt-4o-mini"


def test_request_shape_and_reply(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    seen = {}

    def fake_post(url, json=None, timeout=None, headers=None):
        seen.update(url=url, payload=json, headers=headers)
        return _Resp(200, {"choices": [{"message": {"content": '{"ok": true}'}}]})

    monkeypatch.setattr("httpx.post", fake_post)
    j = Judge(_cfg())
    out = j._openai_reply([np.zeros((30, 40, 3), np.uint8)], "describe", {"type": "object"})
    assert out == '{"ok": true}'
    assert seen["url"] == "https://api.openai.com/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer sk-test"
    content = seen["payload"]["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "describe"}
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert seen["payload"]["response_format"]["type"] == "json_schema"


@pytest.mark.parametrize("key", ["", "mock-replace-with-real-key"])
def test_missing_or_placeholder_key_gives_uncertain_not_exception(monkeypatch, key):
    monkeypatch.setenv("OPENAI_API_KEY", key)
    monkeypatch.setattr("httpx.post", lambda *a, **k: pytest.fail("must not call the API without a key"))
    j = Judge(_cfg())
    assert j.warmup()["ok"] is False
    img = np.zeros((60, 60, 3), np.uint8)
    prop = RegionProposal(id="R1", box=(5, 5, 40, 40), score=1.0, source="dinov2", area_fraction=0.3)
    r = j.judge_region(prop, img[5:40, 5:40], img[5:40, 5:40], img, img, RULES)
    assert r.verdict == Verdict.UNCERTAIN and not r.validated and r.errors and not r.is_mock
    assert any("not configured" in e for e in r.errors)


def test_http_error_is_recorded_without_key_leak(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-value")
    monkeypatch.setattr("httpx.post", lambda *a, **k: _Resp(401, {"error": {"message": "invalid key"}}))
    j = Judge(_cfg())
    raw, errors, _ = j._ask([np.zeros((30, 30, 3), np.uint8)], "p", {}, RULES, False)
    assert raw is None and errors and "401" in errors[0]
    assert all("sk-secret-value" not in e for e in errors)


def test_gameqa_config_env_selects_provider(monkeypatch):
    monkeypatch.setenv("GAMEQA_CONFIG", "configs/openai.yaml")
    cfg = load_config()
    assert cfg["vlm"]["provider"] == "openai" and cfg["proposals"]["max_regions"] == 8
    monkeypatch.delenv("GAMEQA_CONFIG")
    assert load_config()["vlm"]["provider"] == "ollama"


def test_gemini_config_omits_openai_only_detail(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    cfg = load_config("configs/gemini.yaml")
    cfg["vlm"]["cache"] = False
    j = Judge(cfg)
    assert j.model_id.startswith("openai-compatible@generativelanguage.googleapis.com:")
    seen = {}

    def fake_post(url, json=None, timeout=None, headers=None):
        seen.update(url=url, payload=json)
        return _Resp(200, {"choices": [{"message": {"content": "{}"}}]})

    monkeypatch.setattr("httpx.post", fake_post)
    j._openai_reply([np.zeros((30, 30, 3), np.uint8)], "p", {"type": "object"})
    assert seen["url"].endswith("/v1beta/openai/chat/completions")
    assert "detail" not in seen["payload"]["messages"][0]["content"][1]["image_url"]


def test_reasoning_effort_is_sent_and_part_of_cache_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    low, default = Judge(_cfg(reasoning_effort="low")), Judge(_cfg())
    img = [np.zeros((10, 10, 3), np.uint8)]
    assert low._cache_key(img, "p", {}) != default._cache_key(img, "p", {})
    seen = {}

    def fake_post(url, json=None, timeout=None, headers=None):
        seen["payload"] = json
        return _Resp(200, {"choices": [{"message": {"content": "{}"}}]})

    monkeypatch.setattr("httpx.post", fake_post)
    low._openai_reply(img, "p", {})
    assert seen["payload"]["reasoning_effort"] == "low"
    default._openai_reply(img, "p", {})
    assert "reasoning_effort" not in seen["payload"]


def test_transient_503_is_retried_with_backoff(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    j = Judge(_cfg(max_attempts=1))
    calls = {"n": 0}

    def flaky(images, prompt, schema):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise RuntimeError("HTTP 503: model overloaded")
        return '{"ok": true}'

    monkeypatch.setattr(j, "_reply", flaky)
    monkeypatch.setattr("gameqa.vision.judge.time.sleep", lambda s: None)
    raw, errors, _ = j._ask([], "p", {}, RULES, False)
    assert raw == '{"ok": true}' and errors == [] and calls["n"] == 3


def test_permanent_error_is_not_retried_beyond_max_attempts(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    j = Judge(_cfg(max_attempts=2))
    calls = {"n": 0}

    def broken(images, prompt, schema):
        calls["n"] += 1
        raise RuntimeError("HTTP 400: bad request")

    monkeypatch.setattr(j, "_reply", broken)
    monkeypatch.setattr("gameqa.vision.judge.time.sleep", lambda s: None)
    raw, errors, _ = j._ask([], "p", {}, RULES, False)
    assert raw is None and calls["n"] == 2 and len(errors) == 2
