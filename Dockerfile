# Build the UI once; Node is not needed in the running container.
FROM node:24-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OCR_MODEL_DIR=/app/models/OpenThai2.1-OCR-Text-20261118 \
    OCR_BACKEND=onnxruntime \
    HF_HOME=/app/models/.huggingface
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 ocr \
    && useradd --uid 10001 --gid ocr --create-home ocr
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY app/ ./app/
COPY --from=frontend /build/dist ./frontend/dist
COPY LICENSE THIRD_PARTY_NOTICES.md ./
RUN mkdir -p /app/models && chown -R ocr:ocr /app/models
USER ocr
EXPOSE 8091
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8091", "--workers", "1"]
