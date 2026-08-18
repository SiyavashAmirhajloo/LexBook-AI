"""Study session API (V3)."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import Document, StudySession
from app.schemas.study_sessions import (
    StudySessionCreate,
    StudySessionFinishResponse,
    StudySessionListResponse,
    StudySessionStartResponse,
)
from app.services.study_sessions import (
    resolve_studied_section,
    extract_topics,
)

router = APIRouter()

STUDY_VERB_PATTERNS = [
    "finished", "completed", "done with", "studied", "read", "went through",
    "covered", "learned", "just studied", "i finished", "i completed",
]


def _parse_section_label(raw_input: str) -> str | None:
    """Extract a section label from the user's free-text input."""
    text = raw_input.lower().strip().rstrip(".")
    for verb in STUDY_VERB_PATTERNS:
        if verb in text:
            after = text.split(verb, 1)[1].strip()
            # Cut off trailing book references ("... of English Grammar in Use")
            words = after.split()
            if len(words) > 2:
                return " ".join(words[:3]) + "..."
            return after or None
    return text if text else None


@router.post("/study-sessions/start", response_model=StudySessionStartResponse)
async def start_study_session(
    payload: StudySessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Start a study session: resolve the book/section and extract topics."""
    section_label = _parse_section_label(payload.raw_input)

    resolved = await resolve_studied_section(db, payload.raw_input, payload.document_id)

    # Extract topics from matched content
    texts = resolved["texts"]
    extraction = await extract_topics(texts)

    if not payload.document_id and resolved["document_id"]:
        doc_result = await db.execute(
            select(Document).where(Document.id == resolved["document_id"])
        )
        doc = doc_result.scalar_one_or_none()
    else:
        doc = None
        if payload.document_id:
            doc_result = await db.execute(select(Document).where(Document.id == payload.document_id))
            doc = doc_result.scalar_one_or_none()

    session = StudySession(
        raw_input=payload.raw_input,
        document_id=resolved["document_id"] or payload.document_id,
        section_label=section_label,
        page_start=resolved["page_start"],
        page_end=resolved["page_end"],
        topics=extraction["topics"],
        keywords=extraction["keywords"],
        summary=extraction["summary"],
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return StudySessionStartResponse(
        id=session.id,
        raw_input=session.raw_input,
        document_id=session.document_id,
        document_title=doc.title if doc else resolved["document_title"],
        section_label=session.section_label,
        page_start=session.page_start,
        page_end=session.page_end,
        topics=session.topics,
        keywords=session.keywords,
        summary=session.summary,
        started_at=session.started_at,
    )


@router.post("/study-sessions/{session_id}/finish", response_model=StudySessionFinishResponse)
async def finish_study_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Mark a study session complete (records finished_at timestamp)."""
    result = await db.execute(select(StudySession).where(StudySession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")

    from datetime import datetime, timezone
    session.finished_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)

    return StudySessionFinishResponse(
        id=session.id, finished_at=session.finished_at
    )


@router.get("/study-sessions", response_model=list[StudySessionListResponse])
async def list_study_sessions(db: AsyncSession = Depends(get_db)):
    """List all study sessions with extracted topics/keywords."""
    result = await db.execute(
        select(StudySession).order_by(StudySession.started_at.desc())
    )
    sessions = result.scalars().all()

    list_response: list[StudySessionListResponse] = []
    for s in sessions:
        title = None
        if s.document_id:
            doc_result = await db.execute(select(Document.title).where(Document.id == s.document_id))
            title = doc_result.scalar_one_or_none()

        list_response.append(StudySessionListResponse(
            id=s.id,
            raw_input=s.raw_input,
            document_id=s.document_id,
            document_title=title,
            section_label=s.section_label,
            page_start=s.page_start,
            page_end=s.page_end,
            topics=s.topics,
            keywords=s.keywords,
            summary=s.summary,
            started_at=s.started_at,
            finished_at=s.finished_at,
        ))

    return list_response