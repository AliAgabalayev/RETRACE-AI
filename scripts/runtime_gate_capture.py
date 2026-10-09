"""Observe a real local Ollama CLI run without changing inference or decision logic.

Usage: python scripts/runtime_gate_capture.py --evidence-dir <new-directory> --
       analyze --config <yaml> --reference <png> --candidate <png> --rules <yaml> --json

Raw local-provider bodies and exact image bytes stay in the ignored evidence directory.
Headers, environment variables and credentials are never recorded.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("cli_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    cli_args = args.cli_args[1:] if args.cli_args[:1] == ["--"] else args.cli_args
    evidence = args.evidence_dir.resolve()
    # Never overwrite an earlier capture, even when its inference failed.
    evidence.mkdir(parents=True, exist_ok=False)
    calls = []
    original_post = httpx.post

    def recording_post(url, *positional, **kwargs):
        parsed = urlsplit(str(url))
        local_ollama = parsed.hostname in ("localhost", "127.0.0.1") and parsed.path == "/api/chat"
        if not local_ollama:
            return original_post(url, *positional, **kwargs)
        index = len(calls) + 1
        body = kwargs.get("json", {})
        record = {"call": index, "endpoint": str(url), "cache_hit": False,
                  "model": body.get("model"), "images": []}
        request = json.loads(json.dumps(body))
        for mi, message in enumerate(request.get("messages", [])):
            saved_images = []
            for ii, encoded in enumerate(message.get("images", [])):
                raw = base64.b64decode(encoded)
                name = f"call-{index:02d}-message-{mi}-image-{ii}.png"
                (evidence / name).write_bytes(raw)
                info = {"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
                saved_images.append(info)
                record["images"].append(info)
            if "images" in message:
                message["images"] = saved_images
        request_name = f"call-{index:02d}-request.json"
        (evidence / request_name).write_text(json.dumps(request, indent=2), encoding="utf-8")
        record["request"] = request_name
        calls.append(record)
        started = time.perf_counter()
        try:
            response = original_post(url, *positional, **kwargs)
            name = f"call-{index:02d}-response.json"
            (evidence / name).write_bytes(response.content)
            record.update(status_code=response.status_code, response=name)
            return response
        except Exception as exc:
            record["error_type"] = type(exc).__name__
            raise
        finally:
            record["wall_seconds"] = round(time.perf_counter() - started, 4)
            (evidence / "provider-calls.json").write_text(json.dumps(calls, indent=2), encoding="utf-8")

    started = time.perf_counter()
    httpx.post = recording_post
    code = None
    try:
        from gameqa.cli import main as cli_main
        code = cli_main(cli_args)
        return code
    finally:
        httpx.post = original_post
        summary = {"argv": cli_args, "exit_code": code, "cli_wall_seconds": round(time.perf_counter() - started, 4),
                   "provider_call_count": len(calls), "image_provider_call_count": sum(bool(c["images"]) for c in calls),
                   "note": "Observer only; original CLI/provider/policy executed. No response substitution."}
        (evidence / "capture-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
