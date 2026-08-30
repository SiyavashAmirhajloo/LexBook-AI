"""Pydantic schemas for V7 memory endpoints."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LongTermFactResponse(BaseModel):
    id: UUID
    category: str
    fact: str
    source: str
    created_at: datetime


class VocabularyResponse(BaseModel):
    id: UUID
    word: str
    translation: str
    part_of_speech: str
    status: str
    seen_count: int
    topic: str
    last_seen_at: datetime


class WeakTopicSummary(BaseModel):
    topic: str
    mastery: float
    attempts: int
    correct: int


class RecentSessionSummary(BaseModel):
    raw_input: str
    topics: list[str]
    started_at: datetime | None


class MemorySnapshotResponse(BaseModel):
    facts: list[LongTermFactResponse]
    vocabulary: list[VocabularyResponse]
    weak_topics: list[WeakTopicSummary]
    recent_sessions: list[RecentSessionSummary]


class MemorySummaryResponse(BaseModel):
    """Compact single-shot summary suitable for chat prompt injection or UI tooltips."""
    facts: list[LongTermFactResponse]
    vocabulary: list[VocabularyResponse]
    weak_topics: list[WeakTopicSummary]
    fact_count: int
    vocab_count: int
    weak_topic_count: int
