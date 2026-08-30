"""Health endpoints (V9).

- GET /api/v1/health/live: process is up. Use for liveness probes.
- GET /api/v1/health/ready: DB reachable + LLM key configured. Use for
  readiness probes.
- GET /api/v1/health: legacy aggregate (kept for back-compat).
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.core.errors import UpstreamError

router = APIRouter()


@router.get("/health/live")
async def live():
    return {"status": "alive"}


@router.get("/health/ready")
async def ready(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    checks: dict[str, str] = {}
    overall_ok = True

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:  # noqa: BLE001
        checks["database"] = f"error: {e!s}"[:200]
        overall_ok = False

    if settings.google_client_id:
        checks["google_oauth"] = "configured"
    else:
        checks["google_oauth"] = "not configured (Google login disabled)"

    if not overall_ok:
        raise UpstreamError("Service not ready")

    return {"status": "ready", "checks": checks}


@router.get("/health")
async def health_check(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Back-compat endpoint with everything inline."""
    db_ok = False
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": "connected" if db_ok else "disconnected",
    }
