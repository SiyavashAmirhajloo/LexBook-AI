"""Personalization API (V6): flashcards, prompts, quizzes, weak topics."""
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import run_graph
from app.core.db import get_db
from app.models import (
    Flashcard,
    Prompt,
    QuizQuestion,
    StudySession,
    UserProgress,
)
from app.schemas.personalization import (
    FlashcardResponse,
    FlashcardsResponse,
    PromptResponse,
    PromptsResponse,
    QuizAttemptRequest,
    QuizAttemptResponse,
    QuizQuestionResponse,
    QuizResponse,
    RecommendationResponse,
    WeakTopicResponse,
)
from app.services.personalization import (
    generate_flashcards,
    generate_prompts,
    generate_quiz,
    recommendation,
    record_attempt,
    weak_topics,
)

router = APIRouter()


async def _get_session(db: AsyncSession, session_id: UUID) -> StudySession:
    result = await db.execute(select(StudySession).where(StudySession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")
    return session


def _trace(graph_state: dict) -> None:
    print(f"[graph] intent={graph_state.get('intent')} route={graph_state.get('route')}")
    for line in graph_state["trace"]:
        print(f"[graph]   {line}")


# ── Flashcards ──────────────────────────────────────────────────────

@router.post("/study-sessions/{session_id}/flashcards", response_model=FlashcardsResponse)
async def create_flashcards(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Generate ORIGINAL flashcards from this session's studied topics."""
    session = await _get_session(db, session_id)
    cards = await generate_flashcards(session)

    graph_state = await run_graph(
        text=session.raw_input,
        intent="personalize",
        personalization={"flashcards": cards},
    )
    _trace(graph_state)

    db.add_all(cards)
    await db.commit()
    for c in cards:
        await db.refresh(c)

    return FlashcardsResponse(
        study_session_id=session_id,
        cards=[
            FlashcardResponse(
                id=c.id, front=c.front, back=c.back, kind=c.kind, source_topic=c.source_topic
            )
            for c in cards
        ],
    )


@router.get("/study-sessions/{session_id}/flashcards", response_model=FlashcardsResponse)
async def list_flashcards(session_id: UUID, db: AsyncSession = Depends(get_db)):
    await _get_session(db, session_id)
    result = await db.execute(
        select(Flashcard)
        .where(Flashcard.study_session_id == session_id)
        .order_by(Flashcard.created_at)
    )
    cards = result.scalars().all()
    return FlashcardsResponse(
        study_session_id=session_id,
        cards=[
            FlashcardResponse(
                id=c.id, front=c.front, back=c.back, kind=c.kind, source_topic=c.source_topic
            )
            for c in cards
        ],
    )


# ── Prompts (speaking / writing / reading) ──────────────────────────

@router.post("/study-sessions/{session_id}/prompts", response_model=PromptsResponse)
async def create_prompts(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Generate ORIGINAL speaking/writing/reading prompts for this session's topics."""
    session = await _get_session(db, session_id)
    prompts = await generate_prompts(session)

    graph_state = await run_graph(
        text=session.raw_input,
        intent="personalize",
        personalization={"prompts": prompts},
    )
    _trace(graph_state)

    db.add_all(prompts)
    await db.commit()
    for p in prompts:
        await db.refresh(p)

    return PromptsResponse(
        study_session_id=session_id,
        prompts=[
            PromptResponse(
                id=p.id, kind=p.kind, prompt_text=p.prompt_text, source_topic=p.source_topic
            )
            for p in prompts
        ],
    )


@router.get("/study-sessions/{session_id}/prompts", response_model=PromptsResponse)
async def list_prompts(session_id: UUID, db: AsyncSession = Depends(get_db)):
    await _get_session(db, session_id)
    result = await db.execute(
        select(Prompt)
        .where(Prompt.study_session_id == session_id)
        .order_by(Prompt.created_at)
    )
    prompts = result.scalars().all()
    return PromptsResponse(
        study_session_id=session_id,
        prompts=[
            PromptResponse(
                id=p.id, kind=p.kind, prompt_text=p.prompt_text, source_topic=p.source_topic
            )
            for p in prompts
        ],
    )


# ── Quiz ────────────────────────────────────────────────────────────

@router.post("/study-sessions/{session_id}/quiz", response_model=QuizResponse)
async def create_quiz(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Generate an ORIGINAL multiple-choice quiz for this session's topics.

    Correct answers are stored server-side and only revealed after an attempt.
    """
    session = await _get_session(db, session_id)
    questions = await generate_quiz(session)

    graph_state = await run_graph(
        text=session.raw_input,
        intent="personalize",
        personalization={"quiz": questions},
    )
    _trace(graph_state)

    db.add_all(questions)
    await db.commit()
    for q in questions:
        await db.refresh(q)

    return QuizResponse(
        study_session_id=session_id,
        questions=[
            QuizQuestionResponse(
                id=q.id,
                question=q.question,
                choices=json.loads(q.choices),
                source_topic=q.source_topic,
            )
            for q in questions
        ],
    )


@router.post("/quiz/attempt", response_model=QuizAttemptResponse)
async def submit_quiz_attempt(payload: QuizAttemptRequest, db: AsyncSession = Depends(get_db)):
    """Record a quiz answer; updates per-topic mastery used by weak-topic detection."""
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.id == payload.question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Quiz question not found")

    attempt = await record_attempt(db, question, payload.chosen_index)

    row_result = await db.execute(
        select(UserProgress).where(UserProgress.topic == question.source_topic)
    )
    row = row_result.scalar_one()

    return QuizAttemptResponse(
        attempt_id=attempt.id,
        is_correct=attempt.is_correct,
        correct_index=question.correct_index,
        explanation=question.explanation,
        topic_mastery=row.mastery,
        topic_attempts=row.attempts,
    )


# ── Weak topics + recommendation ───────────────────────────────────

@router.get("/weak-topics", response_model=list[WeakTopicResponse])
async def get_weak_topics(limit: int = 5, db: AsyncSession = Depends(get_db)):
    rows = await weak_topics(db, limit=limit)
    return [
        WeakTopicResponse(
            topic=r.topic,
            attempts=r.attempts,
            correct=r.correct,
            mastery=r.mastery,
            last_seen_at=r.last_seen_at,
        )
        for r in rows
    ]


@router.get("/recommendation", response_model=RecommendationResponse)
async def get_recommendation(db: AsyncSession = Depends(get_db)):
    rec = await recommendation(db)
    return RecommendationResponse(recommendation=rec)
