"""Static UI deployment must leave API endpoints intact."""

import importlib

from fastapi.testclient import TestClient

from app.config import Settings
from tests.test_api import FakeEngine


def test_built_frontend_and_api_routes(tmp_path, monkeypatch):
    main = importlib.import_module('app.main')
    monkeypatch.setattr(main, '__file__', str(tmp_path / 'app' / 'main.py'))
    dist = tmp_path / 'frontend' / 'dist'
    (dist / 'assets').mkdir(parents=True)
    (dist / 'index.html').write_text('<html lang="th">OCR Workspace</html>')
    (dist / 'assets' / 'app.js').write_text('console.log("OCR")')
    client = TestClient(main.create_app(Settings(_env_file=None, preload=False), FakeEngine()))
    assert 'OCR Workspace' in client.get('/').text
    assert client.get('/assets/app.js').status_code == 200
    assert client.get('/health').json()['model_state'] == 'ready'
    assert client.get('/v1/info').json()['max_pages'] == 100
    assert client.get('/docs').status_code == 200
    assert client.get('/openapi.json').status_code == 200
    assert client.get('/v1/missing').status_code == 404


def test_api_runs_without_frontend_build(tmp_path, monkeypatch):
    main = importlib.import_module('app.main')
    monkeypatch.setattr(main, '__file__', str(tmp_path / 'app' / 'main.py'))
    client = TestClient(main.create_app(Settings(_env_file=None, preload=False), FakeEngine()))
    assert client.get('/').status_code == 404
    assert client.get('/health').status_code == 200
