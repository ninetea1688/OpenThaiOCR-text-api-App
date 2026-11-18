"""Response models (shown in the OpenAPI docs at /docs)."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class Line(BaseModel):
    text: str
    confidence: float = Field(description="Recognizer confidence, 0..1")
    row: int = Field(description="Reading-order row the line belongs to")
    box: list[list[float]] = Field(description="Four corner points [[x, y], ...] in page-image pixels")
    words: Optional[list[dict[str, Any]]] = Field(None, description="Word boxes (only with include_words=true)")
    reason: Optional[str] = Field(None, description="Why a line was dropped (dropped lines only)")


class PageResult(BaseModel):
    page: int = Field(description="1-based page number in the original file")
    width: Optional[int] = None
    height: Optional[int] = None
    text: str = ""
    lines: list[Line] = []
    dropped: Optional[list[Line]] = Field(None, description="Filtered-out lines (only with include_dropped=true)")
    rotation: int = Field(0, description="Quarter turns applied: 0, 90, 180 or 270")
    text_angle: float = Field(0.0, description="Text angle of the page in degrees")
    error: Optional[str] = None
    elapsed_ms: int = 0


class OCRResponse(BaseModel):
    model: str
    revision: str
    backend: Optional[str]
    filename: Optional[str]
    file_type: str
    total_pages: int = Field(description="Pages in the uploaded file")
    page_count: int = Field(description="Pages processed in this request")
    pages: list[PageResult]
    text: str = Field(description="Text of all processed pages, joined by a blank line")
    elapsed_ms: int


class Health(BaseModel):
    status: str
    model_state: str = Field(description="not_loaded | loading | ready | error")
    model_loaded: bool
    model_error: Optional[str]
    device: str = "cpu"
    backend: Optional[str] = Field(description="openvino | onnxruntime")
    model: str
    revision: str
    version: str = Field(description="API wrapper version; not the OCR model/runtime version. See model and revision for the configured model.")


class Info(Health):
    output: str
    markdown_api: str
    supported_types: list[str]
    max_file_mb: int
    max_pages: int
    pdf_dpi: int
    threads: int
    concurrency: str
    load_seconds: Optional[float]
