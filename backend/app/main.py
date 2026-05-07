from __future__ import annotations

import asyncio
import contextlib
import logging
import sys
import uuid
from collections.abc import AsyncGenerator

# Fix for Windows: psycopg3 requires SelectorEventLoop, not ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import admin, courses, roadmaps, search, subjects, universities, users
from app.services.auth import get_or_create_admin

logger = logging.getLogger(__name__)

# ─── Sentry (no-op when SENTRY_DSN is empty) ─────────────────────────────────
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=False,
    )

# ─── Rate limiter ─────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # ── Fail fast on missing production secrets ────────────────────────────
    if settings.environment == "production":
        _missing = []
        if settings.secret_key in ("change-me-in-production", ""):
            _missing.append("SECRET_KEY")
        if settings.admin_password in ("changeme", ""):
            _missing.append("ADMIN_PASSWORD")
        if settings.admin_email == "admin@example.com":
            _missing.append("ADMIN_EMAIL")
        if not settings.cors_origins or settings.cors_origins == ["http://localhost:3000", "http://localhost:19006"]:
            _missing.append("CORS_ORIGINS")
        if _missing:
            raise RuntimeError(
                f"Missing required production environment variables: {', '.join(_missing)}. "
                "Set them before starting the server."
            )

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

app.state.limiter = limiter

# ─── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Attach a unique request ID to every request for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ─── Exception handlers ───────────────────────────────────────────────────────

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(
        "Unhandled exception [request_id=%s] %s %s",
        request_id,
        request.method,
        request.url,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "request_id": request_id},
    )


# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(courses.router, prefix="/api/v1")
app.include_router(universities.router, prefix="/api/v1")
app.include_router(subjects.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(roadmaps.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


# ─── Health endpoints ─────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
async def health_check():
    """Liveness probe — always returns 200 if the process is running."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """Readiness probe — checks DB and Redis connectivity."""
    from sqlalchemy import text
    from app.database import AsyncSessionLocal

    errors: dict[str, str] = {}

    # Check database
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
    except Exception as exc:
        errors["database"] = str(exc)

    # Check Redis
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
    except Exception as exc:
        errors["redis"] = str(exc)

    if errors:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "errors": errors},
        )
    return {"status": "ready"}
