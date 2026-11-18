"""Turn an uploaded file into page images, one at a time (PDF via pypdfium2, no poppler)."""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Iterator

from PIL import Image, ImageOps

IMAGE_FORMATS = {"JPEG": "jpeg", "PNG": "png", "WEBP": "webp", "TIFF": "tiff", "BMP": "bmp"}
SUPPORTED_TYPES = ["pdf", *IMAGE_FORMATS.values()]

# Guard against decompression bombs (about 16k x 16k pixels).
Image.MAX_IMAGE_PIXELS = 270_000_000


class UnsupportedFile(ValueError):
    pass


@dataclass
class Document:
    file_type: str
    total_pages: int
    _data: bytes
    _dpi: int

    def iter_pages(self, start: int, count: int) -> Iterator[tuple[int, "Image.Image"]]:
        """Yield (1-based page number, RGB image) for pages start..start+count-1."""
        end = min(self.total_pages, start + count - 1)
        if self.file_type == "pdf":
            import pypdfium2 as pdfium

            pdf = pdfium.PdfDocument(self._data)
            try:
                for number in range(start, end + 1):
                    page = pdf[number - 1]
                    try:
                        image = page.render(scale=self._dpi / 72).to_pil().convert("RGB")
                    finally:
                        page.close()
                    yield number, image
            finally:
                pdf.close()
        else:
            with Image.open(io.BytesIO(self._data)) as img:
                for number in range(start, end + 1):
                    img.seek(number - 1)
                    yield number, ImageOps.exif_transpose(img).convert("RGB")


def open_document(data: bytes, dpi: int = 200) -> Document:
    if not data:
        raise UnsupportedFile("Empty file")
    if data[:5] == b"%PDF-" or data[:1024].find(b"%PDF-") != -1:
        import pypdfium2 as pdfium

        try:
            pdf = pdfium.PdfDocument(data)
        except Exception as exc:  # encrypted or broken PDF
            raise UnsupportedFile(f"Cannot open PDF: {exc}") from exc
        try:
            total = len(pdf)
        finally:
            pdf.close()
        if total == 0:
            raise UnsupportedFile("PDF has no pages")
        return Document("pdf", total, data, dpi)
    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = img.format
            frames = getattr(img, "n_frames", 1) if fmt == "TIFF" else 1
            img.verify()
    except Exception as exc:
        raise UnsupportedFile("Not a PDF or a supported image") from exc
    if fmt not in IMAGE_FORMATS:
        raise UnsupportedFile(f"Image format {fmt} is not supported; use one of {', '.join(SUPPORTED_TYPES)}")
    return Document(IMAGE_FORMATS[fmt], frames, data, dpi)
