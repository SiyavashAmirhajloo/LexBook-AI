"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.services.health import check_db

router = APIRouter()


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_db)):
    """Health check endpoint. Returns status and DB connectivity."""
    db_ok = await check_db(session)
    return {
        "status": "ok" if db_ok else "degraded",
        "app": "LexBook AI Backend",
        "database": "connected" if db_ok else "disconnected",
    }