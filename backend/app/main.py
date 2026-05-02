from __future__ import annotations

import contextlib
import logging
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import admin, courses, roadmaps, search, subjects, universities
from app.services.auth import get_or_create_admin

logger = logging.getLogger(__name__)


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
        "Yale, Stanford, NPTEL, Berkeley, and more."
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
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
