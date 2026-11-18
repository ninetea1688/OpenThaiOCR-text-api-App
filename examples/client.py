"""Minimal Python client (standard library only).

Usage: python examples/client.py document.pdf [--url http://127.0.0.1:8091]
"""

import argparse
import json
import mimetypes
import sys
import urllib.request
import uuid
from pathlib import Path


def ocr(path: Path, url: str, **fields) -> dict:
    boundary = uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
             f"Content-Type: {ctype}\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{url}/v1/ocr", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("file")
    a.add_argument("--url", default="http://127.0.0.1:8091")
    a.add_argument("--start-page", type=int, default=1)
    a.add_argument("--max-pages", type=int)
    args = a.parse_args()
    fields = {"start_page": args.start_page}
    if args.max_pages:
        fields["max_pages"] = args.max_pages
    res = ocr(Path(args.file), args.url, **fields)
    for p in res["pages"]:
        print(f"page {p['page']}: {len(p['lines'])} lines, {p['elapsed_ms']} ms"
              + (f", error: {p['error']}" if p["error"] else ""), file=sys.stderr)
    print(res["text"])
