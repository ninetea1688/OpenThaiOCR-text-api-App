"""Settings, read from environment variables (prefix OCR_) or a local .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OCR_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    host: str = "127.0.0.1"
    port: int = 8091

    model_id: str = "iapp/OpenThai2.1-OCR-Text-20261118"
    # Pinned Hugging Face commit, so an upstream change cannot silently alter results.
    model_revision: str = "7092cacf4561679ff9ed19de6821faeb9c96d894"
    # Cache root. Verified snapshots are isolated below snapshots/<source hash>/.
    # Relative paths are taken from the project folder. Default: OCR runtime 2.2.0.
    model_dir: str = "models/OpenThai2.1-OCR-Text-20261118"
    # Download the model (about 6.6 MB) into model_dir if it is missing.
    auto_download: bool = True
    # auto = OpenVINO if installed, else ONNX Runtime (the official Mac guide uses onnxruntime)
    backend: str = "auto"
    # Threads per inference. iApp: one process per core with threads=1 for throughput;
    # their single-script guide uses 2. Above ~2 a single process stops scaling (GIL).
    threads: int = 1
    # Load the model when the server starts (else on the first OCR request).
    preload: bool = True

    max_file_mb: int = 50
    max_pages: int = 100
    pdf_dpi: int = 200  # the official guide renders PDF pages at 200 dpi

    # Browsers on these origins may call the API (regex). Local tool: localhost only.
    cors_origin_regex: str = r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?"

    def resolved_model_dir(self) -> Path:
        p = Path(self.model_dir).expanduser()
        return p if p.is_absolute() else PROJECT_DIR / p


@lru_cache
def get_settings() -> Settings:
    return Settings()
