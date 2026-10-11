"""Free hosting must remain replay-only even if live variables are misconfigured."""
import importlib.util
from pathlib import Path


def test_free_entrypoint_forces_replay_and_removes_credentials(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(root / 'scripts'))
    spec = importlib.util.spec_from_file_location('start_free_replay_test', root / 'scripts/start_free_replay.py')
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
    monkeypatch.setenv('GAMEQA_PUBLIC_REPLAY', '0')
    monkeypatch.setenv('GAMEQA_PUBLIC_STATIC', '1')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'qa-only-not-a-credential')
    monkeypatch.setenv('GEMINI_API_KEY', 'qa-only-not-a-credential')
    import os
    launched = []

    def capture():
        assert os.environ['GAMEQA_PUBLIC_REPLAY'] == '1'
        assert all(name not in os.environ for name in (
            'GAMEQA_PUBLIC_STATIC', 'OPENROUTER_API_KEY', 'GEMINI_API_KEY'))
        launched.append(True)

    monkeypatch.setattr(entry, 'start_application', capture)
    entry.main()
    assert launched == [True]
