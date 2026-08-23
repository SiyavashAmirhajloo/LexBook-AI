"""Pydantic schemas for study sessions API."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StudySessionCreate(BaseModel):
    """Body for starting a study session.

    The user describes what they studied, e.g. "I finished Unit 7 of
    English Grammar in Use" or "I studied Relative Clauses".
    """

    raw_input: str
    document_id: UUID | None = None


class StudySessionStartResponse(BaseModel):
    id: UUID
    raw_input: str
    document_id: UUID | None
    document_title: str | None
    section_label: str | None
    page_start: int | None
    page_end: int | None
    topics: list[str]
    keywords: list[str]
    summary: str | None
    started_at: datetime


class StudySessionFinishResponse(BaseModel):
    id: UUID
    finished_at: datetime


class StudySessionListResponse(BaseModel):
    """One row in the session history list."""

    id: UUID
    raw_input: str
    document_id: UUID | None
    document_title: str | None
    section_label: str | None
    page_start: int | None
    page_end: int | None
    topics: list[str]
    keywords: list[str]
    summary: str | None
    started_at: datetime
    finished_at: datetime | None


class StudyResourceResponse(BaseModel):
    """A curated external learning resource (V5).

    Contains only a link plus an ORIGINAL AI-written summary — never the
    provider's scraped snippet. See docs/architecture.md.
    """

    id: UUID
    topic: str
    url: str
    title: str
    source_domain: str
    summary: str | None
    resource_type: str
    is_reputable: bool
    practice_questions: list[str]


class StudyResourcesResponse(BaseModel):
    """Result of curating web resources for a study session."""

    study_session_id: UUID
    topics: list[str]
    resources: list[StudyResourceResponse]
