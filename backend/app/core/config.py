"""Centralized configuration (V9).

Single Pydantic Settings class. Validation happens at process start so
misconfiguration is loud. All env reads go through here — no scattered
os.getenv() calls in service code.
"""
from __future__ import annotations

import os
import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All env-driven config. Single source of truth."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Environment / runtime ──────────────────────────────────
    environment: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    app_name: str = "LexBook AI"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # ── Database ──────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/lexbook"

    # ── Auth ──────────────────────────────────────────────────
    # JWT secret. Auto-generated for dev if unset so the app boots
    # even with no .env; staging/prod MUST set it explicitly.
    jwt_secret: str = Field(
        default_factory=lambda: os.getenv("JWT_SECRET") or secrets.token_urlsafe(48)
    )
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 14

    # Google OAuth (optional). If unset, Google login is disabled but
    # email/password + guest still work.
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/api/auth/google/callback"
    google_require_verified_email: bool = True

    # Guest mode toggle. If False, /auth/guest 404s.
    allow_guest: bool = True
    jwt_guest_expire_minutes: int = 60 * 8  # 8h

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v  # type: ignore[return-value]


@lru_cache
def get_settings() -> Settings:
    return Settings()
