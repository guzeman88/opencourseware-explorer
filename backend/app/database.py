from __future__ import annotations

from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# asyncpg scheme → psycopg3 scheme mapping
_SCHEME_MAP = {
    "postgresql+asyncpg": "postgresql+psycopg",
    "postgres+asyncpg": "postgresql+psycopg",
}


def _make_engine():
    raw_url = settings.database_url
    parsed = urlparse(raw_url)
    qs = parse_qs(parsed.query)

    hostname = parsed.hostname or ""
    is_internal = ".railway.internal" in hostname

    # Strip SSL-related query params; we pass them via connect_args.
    qs.pop("ssl", None)
    qs.pop("sslmode", None)
    clean_query = urlencode(qs, doseq=True)

    if is_internal:
        # Private network — keep asyncpg, no SSL needed.
        url = urlunparse(parsed._replace(query=clean_query))
        connect_args: dict = {"ssl": False}
    else:
        # Public proxy — switch to psycopg3 (libpq handles Railway SSL correctly).
        scheme = _SCHEME_MAP.get(parsed.scheme, "postgresql+psycopg")
        url = urlunparse(parsed._replace(scheme=scheme, query=clean_query))
        connect_args = {"sslmode": "require"}

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
