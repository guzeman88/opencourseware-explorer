"""Shared database connection helper for scraper utility scripts.

Usage:
    from db_utils import get_connection
    conn = get_connection()

Reads DATABASE_URL from the environment (or .env file if present).
Falls back to the local dev default when DATABASE_URL is not set.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

_DEFAULT_URL = "postgresql://ocw:ocwpass@localhost:5432/opencourseware"


def get_connection(**extra_kwargs):
    """Return a psycopg2 connection using DATABASE_URL env var."""
    import psycopg2  # type: ignore

    url = os.environ.get("DATABASE_URL", _DEFAULT_URL)

    # Strip asyncpg/psycopg scheme prefixes so psycopg2 can parse them
    for prefix in ("postgresql+asyncpg://", "postgres+asyncpg://", "postgresql+psycopg://"):
        if url.startswith(prefix):
            url = "postgresql://" + url[len(prefix):]
            break

    parsed = urlparse(url)
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        dbname=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
        **extra_kwargs,
    )
