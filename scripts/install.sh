#!/usr/bin/env bash
# Install the API on a Mac (Apple silicon or Intel) or Linux.
# Follows iApp's guide: pip install onnxruntime opencv-python-headless pyclipper numpy
# pillow pypdfium2 huggingface_hub, then hf download iapp/OpenThai2.1-OCR-Text-20261118.
set -euo pipefail
cd "$(dirname "$0")/.."

if command -v uv >/dev/null 2>&1; then
  [ -d .venv ] || uv venv --python 3.13 .venv
  PIP=(uv pip install --python .venv/bin/python)
else
  [ -d .venv ] || python3 -m venv .venv
  PIP=(.venv/bin/python -m pip install)
fi

echo "== Installing the runtime and API dependencies"
"${PIP[@]}" -r requirements.txt

echo "== Preparing pinned OCR 2.2.0 snapshot (about 6.6 MB; fine-tuning weights skipped)"
.venv/bin/python -c 'from app.config import get_settings; from app.engine import OCREngine; print(OCREngine(get_settings()).ensure_model_dir())'
echo "== Done. Start with: scripts/run.sh"
