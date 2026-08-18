"""Study session models for V3.

A session records what the user actually studied: which book, which
chapter/unit, when, and what topics/keywords the system extracted from
the studied content.
"""
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.documents import Base


class StudySession(Base):
    """One study session: what the user studied and what was extracted from it."""

    __tablename__ = "study_sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # What the user typed, e.g. "I finished Unit 7 of English Grammar in Use"
    raw_input: Mapped[str] = mapped_column(Text, nullable=False)

    # Resolved book (nullable: the reference may not match anything)
    document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Free-text section label the user referred to, e.g. "Unit 7", "Relative Clauses"
    section_label: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Page range of the matched content (helps the user verify the match)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Extraction results: ["Relative Clauses", "Passive Voice"] / ["defining clause", "whose"]
    topics: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    keywords: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document = relationship("Document")