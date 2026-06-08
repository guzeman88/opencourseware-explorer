from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import sys
from collections.abc import AsyncGenerator

# Fix for Windows: psycopg3 requires SelectorEventLoop, not ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import admin, courses, roadmaps, search, subjects, universities, users
from app.services.auth import get_or_create_admin

logger = logging.getLogger(__name__)

# ─── Sentry ───────────────────────────────────────────────────────────────────
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=False,
    )


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Create tables (dev mode) – in prod use alembic migrations
    if settings.environment != "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Bootstrap admin user (non-fatal – DB may be temporarily unavailable)
    from app.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as db:
            await get_or_create_admin(db)
    except Exception as _exc:
        logger.warning("Admin bootstrap failed (non-fatal): %s", _exc)

    logger.info("OpenCourseWare API started")
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "API for browsing thousands of free university courses from MIT OCW, "
        "Yale, Stanford, Berkeley, and more."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(courses.router, prefix="/api/v1")
app.include_router(universities.router, prefix="/api/v1")
app.include_router(subjects.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(roadmaps.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "git_commit": os.environ.get("RENDER_GIT_COMMIT", "unknown"),
        "git_branch": os.environ.get("RENDER_GIT_BRANCH", "unknown"),
    }
