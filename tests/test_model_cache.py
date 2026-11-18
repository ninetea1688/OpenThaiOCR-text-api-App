"""Prevent stale or incomplete model caches from masquerading as a new release."""

import json

import pytest

from app.config import Settings
from app.engine import OCREngine, REQUIRED_FILES


def settings(tmp_path, **kwargs):
    return Settings(_env_file=None, model_dir=str(tmp_path / 'models'), preload=False, **kwargs)


def fake_download(monkeypatch, calls, incomplete=False):
    def download(repo_id, revision, local_dir, allow_patterns):
        from pathlib import Path
        calls.append((repo_id, revision, local_dir))
        for name in REQUIRED_FILES:
            if incomplete and name == 'rec2.onnx':
                continue
            path = Path(local_dir) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{}' if name == 'config.json' else '')
    monkeypatch.setattr('huggingface_hub.snapshot_download', download)


def test_old_flat_cache_is_not_reused(tmp_path, monkeypatch):
    s = settings(tmp_path)
    for name in REQUIRED_FILES:
        path = s.resolved_model_dir() / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('old model')
    calls = []
    fake_download(monkeypatch, calls)
    directory = OCREngine(s).ensure_model_dir()
    assert len(calls) == 1
    assert directory.parent.name == 'snapshots'
    assert (s.resolved_model_dir() / 'rec.onnx').read_text() == 'old model'
    assert json.loads((directory / '.ocr-source.json').read_text())['revision'] == s.model_revision
    assert OCREngine(s).ensure_model_dir() == directory
    assert len(calls) == 1
    offline = s.model_copy(update={'auto_download': False})
    assert OCREngine(offline).ensure_model_dir() == directory


def test_revision_and_repository_each_have_separate_cache(tmp_path, monkeypatch):
    calls = []
    fake_download(monkeypatch, calls)
    s = settings(tmp_path)
    a = OCREngine(s).ensure_model_dir()
    b = OCREngine(s.model_copy(update={'model_revision': 'b' * 40})).ensure_model_dir()
    c = OCREngine(s.model_copy(update={'model_id': 'other/model'})).ensure_model_dir()
    assert len({a, b, c}) == 3
    assert len(calls) == 3


def test_incomplete_download_is_not_marked_complete(tmp_path, monkeypatch):
    calls = []
    fake_download(monkeypatch, calls, incomplete=True)
    with pytest.raises(FileNotFoundError, match='rec2.onnx'):
        OCREngine(settings(tmp_path)).ensure_model_dir()
    assert not list(tmp_path.rglob('.ocr-source.json'))


def test_missing_file_or_wrong_source_is_repaired(tmp_path, monkeypatch):
    calls = []
    fake_download(monkeypatch, calls)
    engine = OCREngine(settings(tmp_path))
    directory = engine.ensure_model_dir()
    (directory / 'rec2.onnx').unlink()
    engine.ensure_model_dir()
    (directory / '.ocr-source.json').write_text('{}')
    engine.ensure_model_dir()
    assert len(calls) == 3


def test_offline_missing_revision_fails_without_download(tmp_path, monkeypatch):
    calls = []
    fake_download(monkeypatch, calls)
    with pytest.raises(FileNotFoundError, match='verified snapshot'):
        OCREngine(settings(tmp_path, auto_download=False)).ensure_model_dir()
    assert calls == []


def test_failed_background_load_wakes_waiters(tmp_path, monkeypatch):
    engine = OCREngine(settings(tmp_path))
    def fail():
        raise RuntimeError('download failed')
    monkeypatch.setattr(engine, '_load', fail)
    engine._safe_load()
    assert engine._ready.is_set()
    assert engine.state == 'error' and 'download failed' in engine.error
    # Simulate a request that saw state=loading before the background load failed.
    engine.state = 'loading'
    with pytest.raises(RuntimeError, match='download failed'):
        engine.wait_ready(timeout=0.01)


def test_runtime_imports_do_not_reuse_previous_revision(tmp_path, monkeypatch):
    calls = []
    fake_download(monkeypatch, calls)
    engines = [OCREngine(settings(tmp_path, model_revision=revision)) for revision in ['a' * 40, 'b' * 40]]
    for index, engine in enumerate(engines):
        directory = engine.ensure_model_dir()
        (directory / 'runtime' / 'thai_norm.py').write_text(f'VERSION = {index}\n')
        (directory / 'runtime' / 'line_engine.py').write_text(
            'from .thai_norm import VERSION\n'
            'class LineOCR:\n'
            '    def __init__(self, *args, **kwargs): self.backend = str(VERSION)\n'
        )
        engine.load()
    assert [engine.backend for engine in engines] == ['0', '1']
