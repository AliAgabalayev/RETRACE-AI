"""Keyless UI/ZIP smoke and process peak RAM for an isolated replay container."""
import hashlib
import importlib.abc
import json
import os
from pathlib import Path
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
os.environ['GAMEQA_PUBLIC_REPLAY'] = '1'
os.environ.pop('GAMEQA_PUBLIC_STATIC', None)
os.environ.pop('OPENROUTER_API_KEY', None)
os.environ.pop('GEMINI_API_KEY', None)


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch', 'torchvision', 'transformers', 'huggingface_hub'}:
            raise AssertionError(f'Replay attempted a model import: {fullname}')


def main():
    assert 'torch' not in sys.modules
    sys.meta_path.insert(0, NoModels())
    from streamlit.testing.v1 import AppTest
    from gameqa import pipeline

    def forbidden(*args, **kwargs):
        raise AssertionError('Replay attempted new inference')

    pipeline.analyze = forbidden
    pipeline.build_engines = forbidden
    started = time.perf_counter()
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
    assert not app.exception, app.exception
    assert any('replay, no new inference' in item.value for item in app.info)
    assert any('FAIL' in item.value for item in app.error)
    assert any('Rules stored with this run' in item.value for item in app.subheader)
    assert len(app.dataframe) >= 1
    assert len(app.get('download_button')) == 1
    for _ in range(3):
        app.run()
        assert not app.exception
    assert 'torch' not in sys.modules
    archive = ROOT / 'deploy/replay/barrel-replay.zip'
    manifest = json.loads((ROOT / 'deploy/replay/barrel/package.json').read_text())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        prefix = manifest['run_id'] + '/'
        for name, expected in manifest['files'].items():
            assert hashlib.sha256(z.read(prefix + name)).hexdigest() == expected
        evidence = json.loads(z.read(prefix + 'evidence.json'))
        assert evidence['decision']['final'] == 'FAIL'
    result = {'ui_runs':4, 'original_hashes_verified':len(manifest['files']),
              'torch_imported':False, 'vlm_calls':0,
              'ui_and_zip_seconds':round(time.perf_counter()-started,3)}
    if sys.platform == 'linux':
        import resource
        result['process_peak_rss_mib'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)
        assert result['process_peak_rss_mib'] < 512
        peak = Path('/sys/fs/cgroup/memory.peak')
        if peak.is_file():
            result['container_peak_mib'] = round(int(peak.read_text()) / 1024**2, 2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
