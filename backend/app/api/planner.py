"""Planner API (V10): Today's Plan, proactively generated."""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import run_graph
from app.core.db import get_db
from app.services.planner import build_todays_plan

router = APIRouter()


class DueReview(BaseModel):
    word: str
    topic: str
    bucket: int
    interval_days: int
    days_since_seen: int
    reason: str


class WeakTopic(BaseModel):
    topic: str
    mastery: float
    attempts: int
    correct: int


class NextChapter(BaseModel):
    document_title: str
    pages: list[int]
    reason: str


class Readiness(BaseModel):
    ielts_band: float
    toefl_score: float
    weighted_mastery: float
    note: str


class TodaysPlanResponse(BaseModel):
    focus_skill: str
    focus_reason: str
    recommended_topic: str
    topic_reason: str
    weak_topics: list[WeakTopic]
    due_reviews: list[DueReview]
    next_chapter: NextChapter | None
    readiness: Readiness
    recent_topics: list[str]
    summary: str
    summary_source: str
    reasoning: list[str]
    generated_at: datetime


@router.get("/planner/today", response_model=TodaysPlanResponse)
async def todays_plan(db: AsyncSession = Depends(get_db)):
    """Proactive daily plan: what to study next and WHY.

    Deterministic reasoning core (explainable, reproducible) + optional
    LLM narrative. Every recommendation cites its data.
    """
    plan = await build_todays_plan(db)

    graph_state = await run_graph(
        text="daily planning",
        intent="plan",
        plan_result=plan,
    )
    print(f"[graph] intent=plan route={graph_state['route']}")
    for line in graph_state["trace"]:
        print(f"[graph]   {line}")

    return TodaysPlanResponse(**plan, generated_at=datetime.now(UTC))
