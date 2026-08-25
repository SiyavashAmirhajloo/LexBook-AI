"""Personalization models for V6.

Flashcards, prompts, quiz attempts, and a per-topic mastery roll-up that
drives weak-topic detection. Everything here is generated/original content
(no source-book text copied) per docs/architecture.md.
"""
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.documents import Base

# kind: term | grammar | vocab  (drives UI grouping)
_FLASHCARD_KINDS = ("term", "grammar", "vocab")
# kind: speaking | writing | reading | listening
_PROMPT_KINDS = ("speaking", "writing", "reading", "listening")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    study_session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("study_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="term")
    source_topic: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    study_session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("study_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_topic: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    study_session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("study_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    choices: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-encoded list
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    source_topic: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    question_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chosen_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    topic: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mastery: Mapped[float] = mapped_column(nullable=False, default=0.0)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
