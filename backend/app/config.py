"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def _load_env_files() -> None:
    """Load optional .env files without overriding existing process env vars."""
    for candidate in (WORKSPACE_ROOT / ".env", BACKEND_ROOT / ".env"):
        if candidate.is_file():
            load_dotenv(candidate, override=False)


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the Site-to-Cash backend."""

    app_name: str
    app_version: str
    app_env: str
    cors_origins: list[str]
    gemini_api_key: str
    gemini_model: str
    gemini_timeout_seconds: float
    storage_backend: str
    local_data_dir: Path
    max_document_upload_bytes: int = 20 * 1024 * 1024
    max_attachment_upload_bytes: int = 15 * 1024 * 1024
    max_instruction_text_chars: int = 20_000

    @property
    def gemini_configured(self) -> bool:
        """Return whether a Gemini API key is configured (without exposing it)."""
        return bool(self.gemini_api_key.strip())


def _parse_positive_float(raw: str, default: float) -> float:
    try:
        parsed = float(raw.strip())
    except (ValueError, AttributeError):
        return default
    return parsed if parsed > 0 else default


def _parse_positive_int(raw: str, default: int) -> int:
    try:
        parsed = int(raw.strip())
    except (ValueError, AttributeError):
        return default
    return parsed if parsed > 0 else default


def get_settings() -> Settings:
    """Read application settings from environment variables."""
    _load_env_files()

    cors_raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    cors_origins = [origin.strip() for origin in cors_raw.split(",") if origin.strip()]

    # Vercel's deployed function filesystem is read-only. /tmp is writable but
    # ephemeral and is not durable storage; configure a real storage adapter before
    # using this deployment for persistent customer records.
    default_data_dir = "/tmp/site-to-cash" if os.getenv("VERCEL") == "1" else "data"
    raw_data_dir = Path(os.getenv("LOCAL_DATA_DIR", default_data_dir))
    local_data_dir = (
        raw_data_dir if raw_data_dir.is_absolute() else (BACKEND_ROOT / raw_data_dir)
    )

    return Settings(
        app_name=os.getenv("APP_NAME", "Site-to-Cash"),
        app_version="0.1.0",
        app_env=os.getenv("APP_ENV", "development"),
        cors_origins=cors_origins,
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        gemini_timeout_seconds=_parse_positive_float(
            os.getenv("GEMINI_TIMEOUT_SECONDS", "30"), 30.0
        ),
        storage_backend=os.getenv("STORAGE_BACKEND", "local").strip().lower(),
        local_data_dir=local_data_dir,
        max_document_upload_bytes=_parse_positive_int(
            os.getenv("MAX_DOCUMENT_UPLOAD_BYTES", "20971520"), 20 * 1024 * 1024
        ),
        max_attachment_upload_bytes=_parse_positive_int(
            os.getenv("MAX_ATTACHMENT_UPLOAD_BYTES", "15728640"), 15 * 1024 * 1024
        ),
        max_instruction_text_chars=_parse_positive_int(
            os.getenv("MAX_INSTRUCTION_TEXT_CHARS", "20000"), 20_000
        ),
    )
