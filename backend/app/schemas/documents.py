"""Pydantic schemas for documents API."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Public representation of a document."""

    id: UUID
    title: str
    page_count: int
    upload_date: datetime
    file_size: int | None = None

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    """A single similarity search result."""

    chunk_id: UUID
    document_id: UUID
    document_title: str
    page_number: int
    text: str
    score: float = Field(..., description="Cosine similarity score (0-1, higher is better)")


class SearchResponse(BaseModel):
    """Response body for document search."""

    query: str
    results: list[SearchResult]
