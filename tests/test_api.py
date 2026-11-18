"""API tests with a fake engine, so they run without the model."""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.engine import PageError
from app.main import create_app


class FakeEngine:
    def __init__(self, fail_pages=()):
        self.state, self.error, self.backend, self.load_seconds = "ready", None, "onnxruntime", 0.1
        self.calls = 0
        self.fail_pages = set(fail_pages)

    def start_background_load(self):
        pass

    def wait_ready(self, timeout=None):
        pass

    def read_page(self, image):
        self.calls += 1
        if self.calls in self.fail_pages:
            raise PageError("boom")
        return {
            "text": f"หน้า {self.calls}",
            "lines": [{"text": f"หน้า {self.calls}", "confidence": 0.99, "row": 0,
                       "box": [[0, 0], [10, 0], [10, 5], [0, 5]], "words": [{"text": "x"}]}],
            "dropped": [{"text": "~", "confidence": 0.2, "row": 0, "box": [], "reason": "low_confidence"}],
            "rotation": 0,
            "text_angle": 0.0,
        }


def make_client(engine=None, **kw):
    s = Settings(_env_file=None, preload=False, **kw)
    return TestClient(create_app(s, engine or FakeEngine()))


def png_bytes(fmt="PNG"):
    buf = io.BytesIO()
    Image.new("RGB", (60, 30), "white").save(buf, fmt)
    return buf.getvalue()


def pdf_bytes(n):
    buf = io.BytesIO()
    imgs = [Image.new("RGB", (200, 280), "white") for _ in range(n)]
    imgs[0].save(buf, "PDF", save_all=True, append_images=imgs[1:])
    return buf.getvalue()


def test_health_and_info():
    c = make_client()
    h = c.get("/health").json()
    assert h["model_loaded"] and h["device"] == "cpu" and h["backend"] == "onnxruntime"
    assert h["model"] == "iapp/OpenThai2.1-OCR-Text-20261118"
    i = c.get("/v1/info").json()
    assert "8090" in i["markdown_api"] and "pdf" in i["supported_types"]
    assert i["max_pages"] == 100


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP", "TIFF", "BMP"])
def test_image_formats(fmt):
    r = make_client().post("/v1/ocr", files={"file": (f"a.{fmt.lower()}", png_bytes(fmt))})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["page_count"] == 1 and j["text"] == "หน้า 1"
    line = j["pages"][0]["lines"][0]
    assert line["confidence"] == 0.99 and line["words"] is None
    assert j["pages"][0]["dropped"] is None


def test_include_words_and_dropped():
    r = make_client().post("/v1/ocr", files={"file": ("a.png", png_bytes())},
                           data={"include_words": "true", "include_dropped": "true"})
    p = r.json()["pages"][0]
    assert p["lines"][0]["words"] == [{"text": "x"}]
    assert p["dropped"][0]["reason"] == "low_confidence"


def test_pdf_split_and_range():
    c = make_client()
    j = c.post("/v1/ocr", files={"file": ("a.pdf", pdf_bytes(5))},
               data={"start_page": "2", "max_pages": "3"}).json()
    assert j["file_type"] == "pdf" and j["total_pages"] == 5
    assert [p["page"] for p in j["pages"]] == [2, 3, 4]
    assert j["text"] == "หน้า 1\n\nหน้า 2\n\nหน้า 3"


def test_server_page_limit():
    j = make_client(max_pages=2).post("/v1/ocr", files={"file": ("a.pdf", pdf_bytes(4))},
                                      data={"max_pages": "10"}).json()
    assert j["page_count"] == 2


def test_page_error_continues():
    j = make_client(FakeEngine(fail_pages={2})).post("/v1/ocr", files={"file": ("a.pdf", pdf_bytes(3))}).json()
    assert j["page_count"] == 3
    assert j["pages"][1]["error"] == "boom"
    assert j["text"] == "หน้า 1\n\nหน้า 3"


def test_start_page_beyond_end():
    r = make_client().post("/v1/ocr", files={"file": ("a.pdf", pdf_bytes(2))}, data={"start_page": "5"})
    assert r.status_code == 400


def test_unsupported_and_empty():
    c = make_client()
    assert c.post("/v1/ocr", files={"file": ("a.txt", b"hello")}).status_code == 415
    assert c.post("/v1/ocr", files={"file": ("a.txt", b"")}).status_code == 415
    buf = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buf, "GIF")
    assert c.post("/v1/ocr", files={"file": ("a.gif", buf.getvalue())}).status_code == 415


def test_file_too_large():
    r = make_client(max_file_mb=1).post("/v1/ocr", files={"file": ("a.png", b"0" * (1024 * 1024 + 10))})
    assert r.status_code == 413


def test_model_unavailable():
    e = FakeEngine()
    e.state, e.error = "error", "missing det.onnx"

    def fail(timeout=None):
        raise RuntimeError("missing det.onnx")

    e.wait_ready = fail
    r = make_client(e).post("/v1/ocr", files={"file": ("a.png", png_bytes())})
    assert r.status_code == 503


def test_cors_localhost_only():
    c = make_client()
    ok = c.options("/v1/ocr", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    bad = c.options("/v1/ocr", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers
