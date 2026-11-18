"""FastAPI app. Run: uvicorn app.main:app --host 127.0.0.1 --port 8091"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from . import __version__
from .config import Settings, get_settings
from .engine import OCREngine, PageError
from .pages import SUPPORTED_TYPES, UnsupportedFile, open_document
from .schemas import Health, Info, Line, OCRResponse, PageResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ocr.api")


def _line(d: dict, include_words: bool) -> Line:
    return Line(
        text=d.get("text", ""),
        confidence=float(d.get("confidence", 0.0)),
        row=int(d.get("row", 0)),
        box=d.get("box", []),
        words=d.get("words") if include_words else None,
        reason=d.get("reason"),
    )


def create_app(settings: Optional[Settings] = None, engine: Optional[OCREngine] = None) -> FastAPI:
    settings = settings or get_settings()
    engine = engine or OCREngine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.preload and engine.state == "not_loaded":
            engine.start_background_load()
        yield

    app = FastAPI(
        title="OCR Text API",
        version=__version__,
        description=(
            "อ่านข้อความพิมพ์ภาษาไทยและอังกฤษจาก PDF หรือรูปภาพบน CPU "
            "คืนข้อความล้วน พร้อมตำแหน่งและค่าความมั่นใจรายบรรทัด\n\n"
            f"**โมเดลที่ตั้งค่า:** `{settings.model_id}`  \n"
            f"**Revision ที่ตั้งค่า:** `{settings.model_revision}`\n\n"
            "ค่าเริ่มต้นของโปรเจกต์ใช้ **OCR runtime 2.2.0** จาก repository ชื่อ "
            "OpenThai2.1-OCR-Text-20261118 และปิด dewarping ตามต้นทาง "
            "เลขเวอร์ชันข้างชื่อ API และฟิลด์ `version` เป็นรุ่นของ API wrapper "
            "ไม่ใช่รุ่น OCR ตรวจโมเดลที่โหลดและความพร้อมใช้งานได้ที่ `/health` หรือ `/v1/info`\n\n"
            f"**ขีดจำกัด:** {settings.max_file_mb} MB ต่อไฟล์, "
            f"สูงสุด {settings.max_pages} หน้าต่อคำขอ หน้านับจาก 1 "
            "หากไม่ระบุจำนวนหน้า จะอ่านตั้งแต่หน้าเริ่มต้นจนถึงขีดจำกัด\n\n"
            "ไฟล์ประมวลผลบนเซิร์ฟเวอร์นี้ โดยไม่ส่งไปยังบริการ OCR ของ iApp "
            "ผลลัพธ์ไม่สร้างตารางหรือ Markdown; สำหรับงานนั้นใช้ ocr-markdown-api ที่พอร์ต 8090\n\n"
            "**ขอบคุณผู้พัฒนา:** iApp Technology / OpenThai สำหรับโมเดลและ runtime "
            "และ PaddlePaddle / PaddleOCR สำหรับโมเดลพื้นฐาน PP-OCRv6-tiny\n\n"
            f"[Model card และไฟล์ ณ revision ที่ตั้งค่า](https://huggingface.co/{settings.model_id}/tree/{settings.model_revision})"
            f" · [เครดิตและไลเซนส์ต้นทาง](https://huggingface.co/{settings.model_id}/blob/{settings.model_revision}/NOTICE)"
        ),
        lifespan=lifespan,
    )
    app.state.settings, app.state.engine = settings, engine
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=settings.cors_origin_regex,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    def health_dict() -> dict:
        return dict(
            status="ok",
            model_state=engine.state,
            model_loaded=engine.state == "ready",
            model_error=engine.error,
            device="cpu",
            backend=engine.backend,
            model=settings.model_id,
            revision=settings.model_revision,
            version=__version__,
        )

    @app.get(
        "/health", response_model=Health,
        summary="ตรวจสถานะเซิร์ฟเวอร์และโมเดล",
        description="ใช้ model_state=ready เพื่อยืนยันว่าโมเดลพร้อมอ่านเอกสาร; status=ok หมายถึง API ตอบได้เท่านั้น",
    )
    def health():
        return health_dict()

    @app.get(
        "/v1/info", response_model=Info,
        summary="ดูโมเดล revision และข้อจำกัดที่ใช้งานอยู่",
    )
    def info():
        return Info(
            **health_dict(),
            output="Plain text in reading order with a box and confidence per line; no Markdown or tables.",
            markdown_api="For Markdown with tables use ocr-markdown-api: http://127.0.0.1:8090/v1/ocr",
            supported_types=SUPPORTED_TYPES,
            max_file_mb=settings.max_file_mb,
            max_pages=settings.max_pages,
            pdf_dpi=settings.pdf_dpi,
            threads=settings.threads,
            concurrency="one page at a time per process; run more processes for throughput",
            load_seconds=engine.load_seconds,
        )

    @app.post(
        "/v1/ocr", response_model=OCRResponse, response_model_exclude_none=False,
        summary="อ่านข้อความจาก PDF หรือรูปภาพ",
        description=(
            "อัปโหลดหนึ่งไฟล์ด้วย multipart/form-data ระบบตอบเมื่ออ่านครบช่วงหน้าที่เลือก "
            "หากบางหน้าอ่านไม่สำเร็จ จะระบุ pages[].error และอ่านหน้าอื่นต่อ "
            "ข้อความรวม text จะรวมเฉพาะหน้าที่สำเร็จ; API นี้ยังไม่มีตัวเลือกเปิด dewarping"
        ),
        responses={
            400: {"description": "หน้าเริ่มต้นเกินจำนวนหน้าในเอกสาร"},
            413: {"description": "ไฟล์ใหญ่เกินขีดจำกัด"},
            415: {"description": "ไฟล์ว่าง ชนิดไฟล์ไม่รองรับ หรือเปิดเอกสารไม่ได้"},
            503: {"description": "ไม่สามารถโหลดโมเดลได้"},
        },
    )
    async def ocr(
        request: Request,
        file: UploadFile = File(..., description="PDF, JPEG, PNG, WebP, TIFF or BMP"),
        start_page: int = Form(1, ge=1, description="First page to read (1-based)"),
        max_pages: Optional[int] = Form(None, ge=1, description="Pages to read from start_page"),
        include_words: bool = Form(False, description="Also return word boxes for every line"),
        include_dropped: bool = Form(False, description="Also return lines the runtime filtered out"),
    ):
        started = time.perf_counter()
        limit = settings.max_file_mb * 1024 * 1024
        data = await file.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"File is larger than {settings.max_file_mb} MB")
        try:
            doc = await run_in_threadpool(open_document, data, settings.pdf_dpi)
        except UnsupportedFile as exc:
            raise HTTPException(415, str(exc))
        if start_page > doc.total_pages:
            raise HTTPException(400, f"start_page {start_page} is beyond the last page ({doc.total_pages})")
        count = min(max_pages or settings.max_pages, settings.max_pages)

        if engine.state != "ready":
            try:
                await run_in_threadpool(engine.wait_ready)
            except Exception as exc:
                raise HTTPException(503, f"Model is not available: {engine.error or exc}")

        pages: list[PageResult] = []
        iterator = doc.iter_pages(start_page, count)
        while True:
            try:
                item = await run_in_threadpool(next, iterator, None)
            except Exception as exc:  # a page that cannot even be rendered ends the file
                log.warning("Rendering failed after page %d: %s", len(pages), exc)
                pages.append(PageResult(page=start_page + len(pages), error=f"Render failed: {exc}"))
                break
            if item is None:
                break
            number, image = item
            t0 = time.perf_counter()
            result = PageResult(page=number, width=image.width, height=image.height)
            try:
                r = await run_in_threadpool(engine.read_page, image)
                result.text = r.get("text", "")
                result.lines = [_line(x, include_words) for x in r.get("lines", [])]
                if include_dropped:
                    result.dropped = [_line(x, False) for x in r.get("dropped", [])]
                result.rotation = int(r.get("rotation", 0) or 0)
                result.text_angle = float(r.get("text_angle", 0.0) or 0.0)
            except PageError as exc:
                result.error = str(exc)
                log.warning("Page %d of %s failed: %s", number, file.filename, exc)
            result.elapsed_ms = int((time.perf_counter() - t0) * 1000)
            log.info("%s page %d: %d lines, %.2f s", file.filename, number, len(result.lines), result.elapsed_ms / 1000)
            pages.append(result)
            if await request.is_disconnected():
                log.info("Client disconnected; stopping after page %d", number)
                break

        combined = "\n\n".join(p.text for p in pages if p.error is None)
        return OCRResponse(
            model=settings.model_id,
            revision=settings.model_revision,
            backend=engine.backend,
            filename=file.filename,
            file_type=doc.file_type,
            total_pages=doc.total_pages,
            page_count=len(pages),
            pages=pages,
            text=combined,
            elapsed_ms=int((time.perf_counter() - started) * 1000),
        )

    # Register last so API routes and Swagger take precedence over static files.
    frontend = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if (frontend / "index.html").is_file():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")

    return app


app = create_app()
