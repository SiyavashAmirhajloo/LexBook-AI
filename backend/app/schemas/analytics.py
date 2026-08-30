"""Pydantic schemas for V8 Analytics Dashboard."""
from datetime import datetime

from pydantic import BaseModel, Field


class TotalsResponse(BaseModel):
    books_uploaded: int
    pages_studied: int
    sessions_count: int
    sessions_finished: int
    vocabulary_count: int
    facts_count: int
    quiz_attempts: int
    quizzes_correct: int
    weak_topic_count: int
    minutes_studied: int


class SeriesPoint(BaseModel):
    date: str  # ISO date (YYYY-MM-DD)
    value: float


class GrammarTopicPoint(BaseModel):
    topic: str
    mastery: float
    attempts: int
    correct: int


class MistakePoint(BaseModel):
    topic: str
    attempts: int
    correct: int
    mastery: float


class GraphNode(BaseModel):
    id: str
    label: str
    weight: float  # 0..1, larger = more frequently studied


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: int  # co-occurrence count


class TimelineEntry(BaseModel):
    id: str
    started_at: datetime
    finished_at: datetime | None
    raw_input: str
    topics: list[str]


class EstimateResponse(BaseModel):
    label: str
    value: float
    scale: str
    method: str
    inputs: dict[str, float]


class AnalyticsResponse(BaseModel):
    totals: TotalsResponse
    study_time: list[SeriesPoint]
    vocabulary_growth: list[SeriesPoint]
    learning_curve: list[SeriesPoint]
    grammar_topics: list[GrammarTopicPoint]
    mistakes: list[MistakePoint]
    knowledge_graph: dict
    timeline: list[TimelineEntry]
    estimated_ielts: EstimateResponse
    estimated_toefl: EstimateResponse
    scoring_method: str = Field(
        ..., description="Human-readable explanation of the estimation formula"
    )
