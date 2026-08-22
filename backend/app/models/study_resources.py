"""Curated web resource model for V5 Internet Intelligence.

COPYRIGHT: this table stores links plus *original* AI-written summaries.
Scraped snippets and source question text are never persisted — see
docs/architecture.md "Question Sourcing & Copyright".
"""
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.documents import Base


class StudyResource(Base):
    """A curated external learning resource tied to a study session."""

    __tablename__ = "study_resources"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    study_session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("study_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The topic (from V3 extraction) this resource was found for.
    topic: Mapped[str] = mapped_column(String(256), nullable=False)

    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source_domain: Mapped[str] = mapped_column(String(256), nullable=False)

    # AI-written description in original words. NOT the scraped snippet.
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # reading | listening | writing | speaking | grammar | vocabulary | general
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False, default="general")

    # True for the official/educational domains listed in docs/architecture.md.
    is_reputable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Original questions generated from the topic — never copied from the source.
    practice_questions: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    study_session = relationship("StudySession", back_populates="resources")
