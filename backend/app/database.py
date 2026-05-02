from __future__ import annotations

from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _make_engine():
    raw_url = settings.database_url
    parsed = urlparse(raw_url)
    qs = parse_qs(parsed.query)

    # Strip any ssl= param from the URL (passed via connect_args)
    qs.pop("ssl", None)
    clean_query = urlencode(qs, doseq=True)
    url = urlunparse(parsed._replace(query=clean_query))

    # Internal Railway hostname (.railway.internal) uses plain TCP — no SSL needed.
    # External/public connections with SSL should use a sslmode=require DSN instead.
    is_internal = ".railway.internal" in (parsed.hostname or "")
    connect_args: dict = {"ssl": False} if is_internal else {}

    return create_async_engine(
        url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
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
