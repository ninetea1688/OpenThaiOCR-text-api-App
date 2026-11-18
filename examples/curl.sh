#!/usr/bin/env bash
# Examples against a running server (scripts/run.sh). Change FILE to your document.
set -euo pipefail
URL="${OCR_URL:-http://127.0.0.1:8091}"
FILE="${1:-samples/thai_letter.png}"

curl -s "$URL/health"; echo
# Plain text only
curl -s -F "file=@$FILE" "$URL/v1/ocr" | python3 -c 'import json,sys; print(json.load(sys.stdin)["text"])'
# PDF pages 2-3, full JSON (lines with boxes and confidence)
# curl -s -F "file=@document.pdf" -F start_page=2 -F max_pages=2 "$URL/v1/ocr"
