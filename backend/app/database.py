from __future__ import annotations

import ssl
from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _make_engine():
    raw_url = settings.database_url
    parsed = urlparse(raw_url)
    qs = parse_qs(parsed.query)

    # Strip any ssl= / sslmode= params from the URL; pass via connect_args instead.
    qs.pop("ssl", None)
    qs.pop("sslmode", None)
    clean_query = urlencode(qs, doseq=True)
    url = urlunparse(parsed._replace(query=clean_query))

    hostname = parsed.hostname or ""
    if ".railway.internal" in hostname:
        # Private network — plain TCP, no SSL
        connect_args: dict = {"ssl": False}
    else:
        # Public proxy — Railway requires SSL; skip certificate verification
        # because Railway's proxy uses a self-signed / internal cert.
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args = {"ssl": ssl_ctx}

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
