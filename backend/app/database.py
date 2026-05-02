from __future__ import annotations

import ssl as _ssl
from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _make_engine():
    raw_url = settings.database_url
    parsed = urlparse(raw_url)
    qs = parse_qs(parsed.query)

    # Extract ssl param, remove from URL (pass via connect_args with correct type)
    ssl_values = qs.pop("ssl", [])
    ssl_param = ssl_values[0].lower() if ssl_values else ""

    # Rebuild URL without ssl param
    clean_query = urlencode(qs, doseq=True)
    url = urlunparse(parsed._replace(query=clean_query))

    connect_args: dict = {}
    if ssl_param in ("false", "disable", "0"):
        # Explicit no-SSL requested
        connect_args["ssl"] = False
    else:
        # Default: use direct TLS (Railway proxy expects TLS at TCP level, not STARTSSL)
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        connect_args["ssl"] = ctx
        connect_args["direct_tls"] = True

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
