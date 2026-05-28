"""
LabMind AI — Application Configuration
Loads all settings from environment variables via Pydantic BaseSettings.
"""

import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ──
    APP_NAME: str = "LabMind AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ──
    DATABASE_URL: str = "postgresql+psycopg://labmind:labmind_secret@localhost:5432/labmind_db"

    # ── JWT Authentication ──
    JWT_SECRET_KEY: str = "CHANGE-ME-TO-A-REAL-SECRET-KEY-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── CORS ──
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Handle CORS_ORIGINS from .env as JSON string, CSV, or list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ── Gemini ──
    GEMINI_API_KEY: str = ""

    # ── Celery / Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── File Storage ──
    UPLOAD_DIR: str = "uploads"

    # ── V1 Rebuild Engine ──
    YOLO_MODEL_PATH: str = "blood_ai_v2.pt"
    CNN_MODEL_PATH: str = "cell_classifier_v3.pth"
    CNN_2CLASS_MODEL_PATH: str = "cell_classifier_2class.pth"
    CNN_V1_MODEL_PATH: str = "cell_classifier_v1_rebuild.pth"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton — reads .env once at startup."""
    return Settings()
