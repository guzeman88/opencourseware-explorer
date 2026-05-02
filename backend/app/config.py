from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "OpenCourseWare Explorer API"
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = (
        "postgresql+asyncpg://ocw:ocwpass@localhost:5432/opencourseware"
    )

    # Auth / Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week

    # Admin credentials (hashed at startup via passlib)
    admin_email: str = "admin@example.com"
    admin_password: str = "changeme"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:19006"]

    # YouTube
    youtube_api_key: str = ""
    youtube_base_url: str = "https://www.googleapis.com/youtube/v3"

    # Redis (optional cache)
    redis_url: str = "redis://localhost:6379"

    # Pagination
    default_page_size: int = 24
    max_page_size: int = 100

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
