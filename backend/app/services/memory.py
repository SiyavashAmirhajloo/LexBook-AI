"""Memory service for V7 Long-Term Memory.

Provides typed read/write helpers for all 6 memory types from
docs/architecture.md:
  - long-term memory    -> long_term_facts
  - conversation memory -> conversations + messages (V2, read-only here)
  - learning memory    -> study_sessions (V3, read-only here)
  - study progress     -> user_progress (V6, read-only here)
  - weakness memory    -> derived from user_progress
  - vocabulary memory  -> vocabulary

`memory_snapshot()` returns one dict the Memory Agent and the chat prompt
builder can both consume.
"""
import json
import os
import re
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Conversation,
    LongTermFact,
    StudySession,
    UserProgress,
    Vocabulary,
)

# ── Long-term memory ───────────────────────────────────────────────

async def add_fact(
    db: AsyncSession, fact: str, category: str = "fact", source: str = "manual"
) -> LongTermFact | None:
    if not fact.strip():
        return None
    row = LongTermFact(category=category[:32], fact=fact.strip()[:1000], source=source[:32])
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_facts(db: AsyncSession, limit: int = 50) -> list[LongTermFact]:
    result = await db.execute(
        select(LongTermFact).order_by(LongTermFact.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


# ── Vocabulary memory ──────────────────────────────────────────────

async def learn_word(
    db: AsyncSession, word: str, topic: str = "general", translation: str = "",
    part_of_speech: str = "",
) -> Vocabulary | None:
    if not word.strip():
        return None
    word = word.strip()[:128]
    result = await db.execute(select(Vocabulary).where(Vocabulary.word == word))
    row = result.scalar_one_or_none()
    now = datetime.now(UTC)
    if row is None:
        row = Vocabulary(
            word=word, translation=translation[:256], part_of_speech=part_of_speech[:32],
            topic=topic[:256], seen_count=1, last_seen_at=now,
        )
        db.add(row)
    else:
        row.seen_count += 1
        row.last_seen_at = now
        if topic and topic != "general":
            row.topic = topic
    await db.commit()
    await db.refresh(row)
    return row


async def list_vocabulary(
    db: AsyncSession, status: str | None = None, limit: int = 200
) -> list[Vocabulary]:
    stmt = select(Vocabulary).order_by(Vocabulary.last_seen_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Vocabulary.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ── Learning memory (read-only view) ───────────────────────────────

async def recent_sessions(db: AsyncSession, limit: int = 10) -> list[StudySession]:
    result = await db.execute(
        select(StudySession).order_by(StudySession.started_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


# ── Conversation memory (read-only view) ───────────────────────────

async def recent_conversations(db: AsyncSession, limit: int = 10) -> list[Conversation]:
    result = await db.execute(
        select(Conversation).order_by(Conversation.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


# ── Weakness memory (derived from user_progress) ───────────────────

async def weak_topics(
    db: AsyncSession, min_attempts: int = 1, mastery_ceiling: float = 0.5, limit: int = 10
) -> list[UserProgress]:
    """Topics the user has tried and is struggling with."""
    result = await db.execute(
        select(UserProgress)
        .where(UserProgress.attempts >= min_attempts)
        .where(UserProgress.mastery <= mastery_ceiling)
        .order_by(UserProgress.mastery.asc(), UserProgress.last_seen_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ── Unified snapshot for the Memory Agent + RAG prompt ─────────────

async def memory_snapshot(db: AsyncSession, max_facts: int = 8, max_vocab: int = 10) -> dict:
    facts = await list_facts(db, limit=max_facts)
    vocab = await list_vocabulary(db, status="learning", limit=max_vocab)
    weak = await weak_topics(db, limit=5)
    sessions = await recent_sessions(db, limit=3)

    return {
        "facts": [{"category": f.category, "fact": f.fact, "source": f.source} for f in facts],
        "vocabulary": [
            {"word": v.word, "topic": v.topic, "seen_count": v.seen_count} for v in vocab
        ],
        "weak_topics": [
            {"topic": w.topic, "mastery": round(w.mastery, 2), "attempts": w.attempts} for w in weak
        ],
        "recent_sessions": [
            {
                "raw_input": s.raw_input[:100],
                "topics": s.topics or [],
                "started_at": s.started_at.isoformat() if s.started_at else None,
            }
            for s in sessions
        ],
    }


def format_snapshot_for_prompt(snapshot: dict) -> str:
    """Turn the snapshot into a short block the RAG prompt can read."""
    lines: list[str] = []
    if snapshot.get("facts"):
        lines.append("Known user facts:")
        for f in snapshot["facts"][:5]:
            lines.append(f"- [{f['category']}] {f['fact']}")
    if snapshot.get("vocabulary"):
        words = ", ".join(v["word"] for v in snapshot["vocabulary"][:8])
        lines.append(f"Vocabulary the learner is studying: {words}")
    if snapshot.get("weak_topics"):
        weak = ", ".join(
            f"{w['topic']} ({int(w['mastery']*100)}%)" for w in snapshot["weak_topics"][:5]
        )
        lines.append(f"Weak topics (revise these): {weak}")
    if snapshot.get("recent_sessions"):
        last = snapshot["recent_sessions"][0]
        if last.get("topics"):
            lines.append(f"Last studied: {', '.join(last['topics'][:4])}")
    return "\n".join(lines) if lines else "(no prior memory)"


# ── LLM fact/vocab extraction (auto-build memory) ─────────────────

_EXTRACT_PROMPT = """You are updating a learner's long-term memory.

Given their recent message/session text, identify:
- Up to 2 new durable FACTS about the user (preferences, goals, constraints)
  that are worth remembering across sessions.
- Up to 5 vocabulary items they encountered (words/phrases worth tracking).

Return ONLY valid JSON (no markdown fences):
{{
  "facts": [{{"category": "preference|goal|fact", "text": "..."}}],
  "vocabulary": [{{"word": "...", "topic": "..."}}]
}}

Text to analyze:
{text}
"""


async def extract_memories(text: str) -> dict:
    """Ask the LLM for new facts + vocabulary from a message. Returns dict with
    'facts' and 'vocabulary' lists; empty lists on failure or no LLM."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not text.strip():
        return {"facts": [], "vocabulary": []}
    model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )
    try:
        prompt = _EXTRACT_PROMPT.format(text=text[:3000])
        body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
        return json.loads(raw)
    except Exception:
        return {"facts": [], "vocabulary": []}
