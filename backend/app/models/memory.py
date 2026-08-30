"""Memory models for V7 Long-Term Memory.

Two new structured tables (long_term_facts and vocabulary). The remaining
4 memory types from docs/architecture.md (conversation, learning, study
progress, weakness) are already covered by V2/V3/V6 tables — the
Memory Agent simply reads/writes them.

Why these two are structured (not embedded text):
- Sparse, list-style data: exact-match lookups, indexed by word/fact value.
- Small row sizes, frequent reads: SQL > pgvector for a 200-word list.
- No semantic-search use case in the V7 scope.
"""
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.documents import Base


class LongTermFact(Base):
    """A small durable fact about the user: a preference, goal, or statement."""

    __tablename__ = "long_term_facts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    category: Mapped[str] = mapped_column(String(32), nullable=False)  # preference | goal | fact
    fact: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # chat | study_session | manual
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class Vocabulary(Base):
    """A word/phrase the learner is tracking, with study state."""

    __tablename__ = "vocabulary"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    word: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    translation: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    part_of_speech: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    # status: learning | known | familiar
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="learning")
    seen_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    topic: Mapped[str] = mapped_column(String(256), nullable=False, default="general")
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
