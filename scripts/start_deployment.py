"""Portable Streamlit entrypoint; frozen config, writable storage, keyless replay."""
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prepare_deployment import prepare


def main():
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    os.environ["GAMEQA_CONFIG"] = "configs/openrouter_gemini_pilot.yaml"
    public_replay = os.environ.get("GAMEQA_PUBLIC_REPLAY", "").strip() == "1"
    prepare(public_replay=public_replay)
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if public_replay:
        os.environ.pop("OPENROUTER_API_KEY", None)
        print("Public recorded replay; inference and reference approval disabled")
    else:
        print("Live credential configured" if key and not key.startswith("mock-") else "Saved replay available; live inference requires OPENROUTER_API_KEY")
    raise SystemExit(subprocess.call([sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.address", "0.0.0.0", "--server.port", os.environ.get("PORT", "8501"),
        "--server.headless", "true", "--browser.gatherUsageStats", "false"]))


if __name__ == "__main__":
    main()
