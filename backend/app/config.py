from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, EnvSettingsSource, SettingsConfigDict


class _CorsAwareEnvSource(EnvSettingsSource):
    """Custom env source that parses CORS_ORIGINS as comma-separated or JSON array."""

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == "cors_origins" and isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(s).strip() for s in parsed if str(s).strip()]
            except (json.JSONDecodeError, ValueError):
                pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return super().prepare_field_value(field_name, field, value, value_is_complex)


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
    access_token_expire_minutes: int = 60 * 8  # 8 hours

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

    # Sentry (optional error tracking; leave empty to disable)
    sentry_dsn: str = ""

    # Pagination
    default_page_size: int = 24
    max_page_size: int = 100

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
        return (
            init_settings,
            _CorsAwareEnvSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
