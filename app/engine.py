"""Model wrapper around iApp's own runtime (runtime/line_engine.py, shipped with the model).

Follows iApp's official guide (https://iapp.co.th/en/blog/openthai2p0-ocr-how-to-run):
call `LineOCR(model_dir, threads=N)`, then `ocr.read(PIL image)`. Their runtime is
used unchanged under a snapshot-specific package namespace; this file loads it
once and serialises calls.

The runtime picks OpenVINO when it is installed and ONNX Runtime otherwise. The Mac guide
installs onnxruntime, and so does scripts/install.sh. Set OCR_BACKEND to force one.
"""

from __future__ import annotations

import importlib
import importlib.util
import hashlib
import json
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional

from .config import Settings

log = logging.getLogger("ocr.engine")

REQUIRED_FILES = [
    "det.onnx", "rec.onnx", "rec2.onnx", "rec_dict.txt", "config.json",
    "runtime/__init__.py", "runtime/line_engine.py", "runtime/thai_norm.py", "runtime/dewarp.py",
]
# Only what inference needs: pytorch/rec_weights.pt is for fine-tuning.
ALLOW_PATTERNS = ["*.onnx", "*.yml", "*.json", "*.txt", "runtime/*", "NOTICE", "README.md", "SHA256SUMS"]


class PageError(Exception):
    """One page could not be read; the request continues with the next page."""


class OCREngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.state = "not_loaded"  # not_loaded | loading | ready | error
        self.error: Optional[str] = None
        self.backend: Optional[str] = None
        self.load_seconds: Optional[float] = None
        self._ocr = None
        self._load_lock = threading.Lock()
        self._infer_lock = threading.Lock()  # one page at a time per process
        self._ready = threading.Event()

    # ---------- loading ----------
    def start_background_load(self) -> None:
        threading.Thread(target=self._safe_load, name="model-loader", daemon=True).start()

    def _safe_load(self) -> None:
        try:
            self.load()
        except Exception:  # state and error are recorded in load()
            pass

    def load(self) -> None:
        with self._load_lock:
            if self.state == "ready":
                return
            self.state, self.error = "loading", None
            self._ready.clear()
            started = time.perf_counter()
            try:
                self._load()
            except Exception as exc:
                self.state, self.error = "error", f"{type(exc).__name__}: {exc}"
                self._ready.set()  # Wake requests waiting on a failed background download/load.
                log.exception("Model load failed")
                raise
            self.load_seconds = round(time.perf_counter() - started, 2)
            self.state = "ready"
            self._ready.set()
            log.info("Model ready (%s, threads=%d) in %.2f s", self.backend, self.settings.threads, self.load_seconds)

    def ensure_model_dir(self) -> Path:
        s = self.settings
        source = {"model_id": s.model_id, "revision": s.model_revision}
        key = hashlib.sha256(json.dumps(source, sort_keys=True).encode()).hexdigest()
        root = s.resolved_model_dir()
        d = root / "snapshots" / key
        marker = d / ".ocr-source.json"

        def complete() -> bool:
            try:
                return json.loads(marker.read_text()) == source and all((d / f).is_file() for f in REQUIRED_FILES)
            except (OSError, ValueError):
                return False

        if complete():
            return d
        if not s.auto_download:
            raise FileNotFoundError(
                f"No complete verified snapshot for {s.model_id}@{s.model_revision} in {d}; "
                "prepare it with OCR_AUTO_DOWNLOAD=true before running offline"
            )

        # A shared Docker volume can be used by multiple processes. Publish the
        # source marker only after the entire requested snapshot is available.
        from filelock import FileLock

        root.mkdir(parents=True, exist_ok=True)
        with FileLock(str(root / ".download.lock")):
            if complete():
                return d
            from huggingface_hub import snapshot_download

            marker.unlink(missing_ok=True)
            log.info("Downloading %s@%s into %s", s.model_id, s.model_revision, d)
            snapshot_download(s.model_id, revision=s.model_revision, local_dir=str(d), allow_patterns=ALLOW_PATTERNS)
            missing = [f for f in REQUIRED_FILES if not (d / f).is_file()]
            if missing:
                raise FileNotFoundError(f"Downloaded snapshot is incomplete: {', '.join(missing)}")
            temporary = marker.with_suffix(".tmp")
            temporary.write_text(json.dumps(source, sort_keys=True) + "\n")
            temporary.replace(marker)
        return d

    def _load(self) -> None:
        d = self.ensure_model_dir()
        # Relative imports in upstream runtime stay inside this snapshot. Using
        # the global name "runtime" can silently reuse an older loaded version.
        namespace = "_ocr_runtime_" + hashlib.sha256(str(d.resolve()).encode()).hexdigest()
        if namespace not in sys.modules:
            spec = importlib.util.spec_from_file_location(
                namespace, d / "runtime" / "__init__.py",
                submodule_search_locations=[str(d / "runtime")],
            )
            package = importlib.util.module_from_spec(spec)
            sys.modules[namespace] = package
            spec.loader.exec_module(package)
        line_engine = importlib.import_module(f"{namespace}.line_engine")
        overrides: dict[str, Any] = {}
        if self.settings.backend.lower() != "auto":
            overrides["runtime"] = {"backend": self.settings.backend.lower()}
        self._ocr = line_engine.LineOCR(str(d), threads=self.settings.threads, **overrides)
        self.backend = getattr(self._ocr, "backend", None)

    def wait_ready(self, timeout: Optional[float] = None) -> None:
        """Block until the model is loaded (loading it now if nobody has started)."""
        if self.state == "ready":
            return
        if self.state in ("not_loaded", "error"):
            self.load()
            return
        if not self._ready.wait(timeout):
            raise TimeoutError("Model is still loading")
        if self.state != "ready":
            raise RuntimeError(self.error or "Model failed to load")

    # ---------- inference ----------
    def read_page(self, image) -> dict[str, Any]:
        """Read one PIL image -> LineOCR result dict. Raises PageError if it fails."""
        self.wait_ready()
        with self._infer_lock:
            try:
                return self._ocr.read(image.convert("RGB"))
            except Exception as exc:
                log.exception("Page failed")
                raise PageError(f"{type(exc).__name__}: {exc}") from exc
