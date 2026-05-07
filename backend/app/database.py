from __future__ import annotations

from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# asyncpg scheme → psycopg3 scheme mapping
_SCHEME_MAP = {
    "postgresql+asyncpg": "postgresql+psycopg",
    "postgres+asyncpg": "postgresql+psycopg",
    "postgresql": "postgresql+psycopg",
    "postgres": "postgresql+psycopg",
}


def _make_engine():
    raw_url = settings.database_url
    parsed = urlparse(raw_url)
    qs = parse_qs(parsed.query)

    # Strip SSL-related query params; we pass them via connect_args.
    qs.pop("ssl", None)
    qs.pop("sslmode", None)
    clean_query = urlencode(qs, doseq=True)

    # Always use psycopg3 (libpq) — handles Railway SSL correctly on both
    # internal (.railway.internal) and public (proxy) connections.
    scheme = _SCHEME_MAP.get(parsed.scheme, "postgresql+psycopg")
    url = urlunparse(parsed._replace(scheme=scheme, query=clean_query))

    hostname = parsed.hostname or ""
    _local = hostname in ("localhost", "127.0.0.1", "::1", "db")
    if ".railway.internal" in hostname or "rlwy.net" in hostname or _local:
        # Railway connections and local dev: plain TCP, no SSL.
        connect_args: dict = {"sslmode": "disable", "connect_timeout": 10}
    else:
        connect_args = {"sslmode": "require", "connect_timeout": 10}

    return create_async_engine(
        url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args=connect_args,
    )


engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
