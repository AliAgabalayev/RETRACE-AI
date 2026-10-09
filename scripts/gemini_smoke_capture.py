"""One existing-CLI smoke run; bounded Gemini calls and credential-free evidence.

No response substitution or inference/policy changes. Stop network calls after quota
exhaustion or the generation budget. Each capture directory must be new.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    parser.add_argument('cli_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.cli_args[1:] if args.cli_args[:1] == ['--'] else args.cli_args
    root = args.evidence_dir
    root.mkdir(parents=True, exist_ok=False)
    secret = os.environ.get('GEMINI_API_KEY', '')
    if not secret:
        raise RuntimeError('GEMINI_API_KEY missing; no provider calls attempted')

    def safe(text):
        return text.replace(secret, '[REDACTED]')

    def save(name, data):
        (root / name).write_text(safe(json.dumps(data, indent=2, ensure_ascii=False)), encoding='utf-8')

    calls = []
    stopped = False
    original = httpx.post

    def capture(url, *pos, **kw):
        nonlocal stopped
        endpoint = urlsplit(str(url))
        if endpoint.hostname != 'generativelanguage.googleapis.com' or not endpoint.path.endswith('/chat/completions'):
            return original(url, *pos, **kw)
        if stopped or len(calls) >= 8:
            raise RuntimeError('Gemini smoke budget/quota stop; no additional network request')
        request = json.loads(json.dumps(kw.get('json', {})))
        index = len(calls) + 1
        images = []
        for mi, message in enumerate(request.get('messages', [])):
            for ii, item in enumerate(message.get('content', [])):
                if item.get('type') == 'image_url':
                    raw = base64.b64decode(item['image_url']['url'].split(',', 1)[1])
                    name = f'call-{index:02d}-message-{mi}-image-{ii}.png'
                    (root / name).write_bytes(raw)
                    facts = {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}
                    item['image_url']['url'] = facts
                    images.append(facts)
        record = {'call': index, 'cache_hit': False, 'model': request.get('model'), 'images': images}
        calls.append(record)
        save(f'call-{index:02d}-request.json', request)
        started = time.perf_counter()
        try:
            response = original(url, *pos, **kw)
            # Provider bodies and propagated exceptions must never echo the key.
            response._content = safe(response.text).encode('utf-8')
            save(f'call-{index:02d}-response.json', response.json())
            record['status_code'] = response.status_code
            if response.status_code in (429, 503):
                stopped = True
            return response
        except Exception as exc:
            record['error_type'] = type(exc).__name__
            stopped = True
            raise RuntimeError(safe(str(exc))) from None
        finally:
            record['seconds'] = round(time.perf_counter() - started, 4)
            save('provider-calls.json', calls)

    httpx.post = capture
    start = time.perf_counter()
    code = None
    try:
        from gameqa.cli import main as cli_main
        code = cli_main(argv)
        return code
    finally:
        httpx.post = original
        save('summary.json', {'exit_code': code, 'calls': len(calls), 'wall_seconds': time.perf_counter() - start,
                              'quota_or_failure_stop': stopped, 'fresh_namespace': True,
                              'note': 'Existing CLI/provider/policy; headers and credentials never persisted.'})


if __name__ == '__main__':
    raise SystemExit(main())
