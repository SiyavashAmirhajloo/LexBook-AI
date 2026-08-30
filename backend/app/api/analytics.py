"""Analytics API (V8)."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics import compute_snapshot

router = APIRouter()


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(db: AsyncSession = Depends(get_db)):
    """Return a single read-only snapshot of every tracked metric.

    Pulls only from existing V2/V3/V6/V7 tables — no parallel tracking system.
    """
    return await compute_snapshot(db)
