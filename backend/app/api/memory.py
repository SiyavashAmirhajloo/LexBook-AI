"""Memory API (V7 Long-Term Memory).

- GET /memory/snapshot    full snapshot (facts, vocab, weak topics, recent sessions)
- GET /memory/summary     compact snapshot for prompt injection
- GET /memory/facts       durable user facts
- GET /memory/vocabulary  tracked words
- POST /memory/facts      add a fact manually
- POST /memory/vocabulary add/mark a vocabulary word
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import LongTermFact, Vocabulary
from app.schemas.memory import (
    LongTermFactResponse,
    MemorySnapshotResponse,
    MemorySummaryResponse,
    RecentSessionSummary,
    VocabularyResponse,
    WeakTopicSummary,
)
from app.services.memory import (
    add_fact,
    learn_word,
    list_facts,
    list_vocabulary,
    recent_sessions,
    weak_topics,
)

router = APIRouter()


# ── Input models ───────────────────────────────────────────────────

class AddFactRequest(BaseModel):
    fact: str
    category: str = "fact"
    source: str = "manual"


class AddVocabularyRequest(BaseModel):
    word: str
    topic: str = "general"
    translation: str = ""
    part_of_speech: str = ""


# ── Mapping helpers ────────────────────────────────────────────────

def _fact_response(f: LongTermFact) -> LongTermFactResponse:
    return LongTermFactResponse(
        id=f.id, category=f.category, fact=f.fact, source=f.source, created_at=f.created_at
    )


def _vocab_response(v: Vocabulary) -> VocabularyResponse:
    return VocabularyResponse(
        id=v.id, word=v.word, translation=v.translation, part_of_speech=v.part_of_speech,
        status=v.status, seen_count=v.seen_count, topic=v.topic, last_seen_at=v.last_seen_at,
    )


# ── Routes ────────────────────────────────────────────────────────

@router.get("/memory/snapshot", response_model=MemorySnapshotResponse)
async def get_memory_snapshot(db: AsyncSession = Depends(get_db)):
    return MemorySnapshotResponse(
        facts=[_fact_response(f) for f in (await list_facts(db))],
        vocabulary=[_vocab_response(v) for v in (await list_vocabulary(db))],
        weak_topics=[
            WeakTopicSummary(
                topic=w.topic, mastery=w.mastery, attempts=w.attempts, correct=w.correct
            ) for w in (await weak_topics(db))
        ],
        recent_sessions=[
            RecentSessionSummary(
                raw_input=s.raw_input, topics=s.topics or [], started_at=s.started_at
            ) for s in (await recent_sessions(db))
        ],
    )


@router.get("/memory/summary", response_model=MemorySummaryResponse)
async def get_memory_summary(db: AsyncSession = Depends(get_db)):
    facts = await list_facts(db, limit=8)
    vocab = await list_vocabulary(db, status="learning", limit=10)
    weak = await weak_topics(db, limit=5)
    return MemorySummaryResponse(
        facts=[_fact_response(f) for f in facts],
        vocabulary=[_vocab_response(v) for v in vocab],
        weak_topics=[
            WeakTopicSummary(
                topic=w.topic, mastery=w.mastery, attempts=w.attempts, correct=w.correct
            ) for w in weak
        ],
        fact_count=len(facts),
        vocab_count=len(vocab),
        weak_topic_count=len(weak),
    )


@router.get("/memory/facts", response_model=list[LongTermFactResponse])
async def list_facts_endpoint(db: AsyncSession = Depends(get_db)):
    return [_fact_response(f) for f in (await list_facts(db))]


@router.post("/memory/facts", response_model=LongTermFactResponse, status_code=201)
async def add_fact_endpoint(payload: AddFactRequest, db: AsyncSession = Depends(get_db)):
    row = await add_fact(db, payload.fact, category=payload.category, source=payload.source)
    if not row:
        raise HTTPException(status_code=400, detail="Fact cannot be empty")
    return _fact_response(row)


@router.get("/memory/vocabulary", response_model=list[VocabularyResponse])
async def list_vocab_endpoint(
    status: str | None = None, db: AsyncSession = Depends(get_db)
):
    return [_vocab_response(v) for v in (await list_vocabulary(db, status=status))]


@router.post("/memory/vocabulary", response_model=VocabularyResponse, status_code=201)
async def add_vocab_endpoint(
    payload: AddVocabularyRequest, db: AsyncSession = Depends(get_db)
):
    row = await learn_word(
        db, payload.word, topic=payload.topic, translation=payload.translation,
        part_of_speech=payload.part_of_speech,
    )
    if not row:
        raise HTTPException(status_code=400, detail="Word cannot be empty")
    return _vocab_response(row)
