"""List the model IDs an OpenAI-compatible VLM endpoint offers (never prints the API key).

Usage: .venv/bin/python scripts/list_models.py --config configs/gemini.yaml [--filter flash]
"""

from __future__ import annotations

import argparse
import sys

import httpx

from gameqa.config import load_config
from gameqa.vision.judge import Judge


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", required=True)
    ap.add_argument("--filter", default="", help="only show IDs containing this text")
    args = ap.parse_args()
    judge = Judge(load_config(args.config))
    if judge.provider != "openai":
        print("config is not an OpenAI-compatible provider", file=sys.stderr)
        return 2
    try:
        key = judge._api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    r = httpx.get(f"{judge.base_url}/models", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    if r.status_code >= 400:
        print(f"HTTP {r.status_code}: {r.text[:300]}", file=sys.stderr)
        return 1
    ids = sorted(m.get("id", "") for m in r.json().get("data", []))
    for mid in ids:
        if args.filter in mid:
            print(mid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
