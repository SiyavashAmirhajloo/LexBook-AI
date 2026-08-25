"""Personalization service (V6): generate flashcards, prompts, and quizzes.

All generated content is ORIGINAL (never copied from a source book) per
docs/architecture.md. If Gemini is unavailable, heuristic generators fall
back so the pipeline never blocks.

Quiz attempts update `user_progress`, which feeds `weak_topics()`.
"""
import asyncio
import json
import os
import re
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Flashcard,
    Prompt,
    QuizAttempt,
    QuizQuestion,
    StudySession,
    UserProgress,
)

# ── LLM caller (Gemini REST, JSON-only) ────────────────────────────

async def _llm_json(prompt: str) -> dict | None:
    """Call Gemini for structured JSON. One retry on transient 5xx.

    ponytail: single retry — free-tier 503s are bursts; a longer backoff
    queue belongs in V9 production hardening.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(url, json=body)
        if resp.status_code >= 500:  # transient (e.g. "high demand" UNAVAILABLE)
            await asyncio.sleep(4)
            resp = await client.post(url, json=body)
    if resp.status_code != 200:
        print(f"[personalization] LLM call failed: {resp.status_code} {resp.text[:150]}")
        return None
    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


# ── Flashcards ──────────────────────────────────────────────────────

_FLASHCARD_PROMPT = """Generate ORIGINAL English-learning flashcards for these topics.

Topics (with optional short context):
{topics_context}

Return ONLY valid JSON (no markdown fences):
{{
  "cards": [
    {{"front": "<term or question>",
      "back": "<original explanation in your own words>",
      "kind": "term|grammar|vocab",
      "topic": "<one of the topics above>"}},
    ...
  ]
}}

Generate 2-3 cards per topic. Cards must be original — never copy any source.
"""


async def generate_flashcards(session: StudySession, per_topic: int = 3) -> list[Flashcard]:
    topics = session.topics or [session.raw_input[:80]]
    topics_context = "\n".join(f"- {t}" for t in topics)
    parsed = await _llm_json(_FLASHCARD_PROMPT.format(topics_context=topics_context))
    cards = (parsed or {}).get("cards", []) if parsed else []

    if not cards:
        # Heuristic fallback so the pipeline never returns empty.
        cards = [
            {
                "front": t,
                "back": f"Briefly explain the key idea behind '{t}' in your own words.",
                "kind": "term",
                "topic": t,
            }
            for t in topics
        ]

    rows = [
        Flashcard(
            study_session_id=session.id,
            front=str(c.get("front", "")).strip()[:1000],
            back=str(c.get("back", "")).strip()[:2000],
            kind=str(c.get("kind", "term")).strip().lower()[:32],
            source_topic=str(c.get("topic", topics[0])).strip()[:256],
        )
        for c in cards
        if str(c.get("front", "")).strip()
    ]
    return rows[: per_topic * max(1, len(topics))]


# ── Prompts (speaking / writing / reading) ──────────────────────────

_PROMPT_PROMPT = """Generate ORIGINAL IELTS-style practice prompts for these topics.

Topics (with optional short context):
{topics_context}

Return ONLY valid JSON:
{{
  "prompts": [
    {{"kind": "speaking|writing|reading", "topic": "<topic>", "prompt_text": "<original prompt>"}},
    ...
  ]
}}

Rules:
- Speaking prompts: original Part 1/2/3 style questions (3 questions).
- Writing prompts: original Task 1 OR Task 2 essay question (2 prompts).
- Reading prompts: original short passage + comprehension question (2 prompts).
- Total ~7 prompts. Never reproduce source questions.
"""


async def generate_prompts(session: StudySession) -> list[Prompt]:
    topics = session.topics or [session.raw_input[:80]]
    topics_context = "\n".join(f"- {t}" for t in topics)
    parsed = await _llm_json(_PROMPT_PROMPT.format(topics_context=topics_context))
    items = (parsed or {}).get("prompts", []) if parsed else []

    if not items:
        items = [
            {
                "kind": "speaking",
                "topic": topics[0],
                "prompt_text": (
                    f"Describe a real-world example where {topics[0]} "
                    "mattered in your daily life."
                ),
            },
            {
                "kind": "writing",
                "topic": topics[0],
                "prompt_text": (
                    f"Write a 250-word essay on the importance of {topics[0]} "
                    "for English learners."
                ),
            },
        ]

    rows = [
        Prompt(
            study_session_id=session.id,
            prompt_text=str(p.get("prompt_text", "")).strip()[:2000],
            kind=str(p.get("kind", "speaking")).strip().lower()[:32],
            source_topic=str(p.get("topic", topics[0])).strip()[:256],
        )
        for p in items
        if str(p.get("prompt_text", "")).strip()
    ]
    return rows


# ── Quiz (multiple-choice with correct_index + explanation) ────────

_QUIZ_PROMPT = """Generate ORIGINAL multiple-choice questions about these topics.

Topics:
{topics_context}

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "topic": "<topic>",
      "question": "<original question>",
      "choices": ["<A>", "<B>", "<C>", "<D>"],
      "correct_index": 0..3,
      "explanation": "<why this choice is right, in your own words>"
    }},
    ...
  ]
}}

Rules:
- Generate exactly 5 original questions spread across the topics.
- Choices are LLM-invented distractors; NEVER copy from any source book.
- Exactly one correct choice per question.
"""


async def generate_quiz(session: StudySession) -> list[QuizQuestion]:
    topics = session.topics or [session.raw_input[:80]]
    topics_context = "\n".join(f"- {t}" for t in topics)
    parsed = await _llm_json(_QUIZ_PROMPT.format(topics_context=topics_context))
    items = (parsed or {}).get("questions", []) if parsed else []

    if not items:
        items = [
            {
                "topic": topics[0],
                "question": f"Which option best describes {topics[0]}?",
                "choices": ["Option A", "Option B", "Option C", "Option D"],
                "correct_index": 0,
                "explanation": (
                    "Heuristic placeholder; rerun with an LLM provider for real items."
                ),
            }
        ]

    rows: list[QuizQuestion] = []
    for q in items:
        choices = q.get("choices") or []
        correct_index = int(q.get("correct_index", 0))
        if not (isinstance(choices, list) and len(choices) == 4 and 0 <= correct_index <= 3):
            continue
        rows.append(
            QuizQuestion(
                study_session_id=session.id,
                question=str(q.get("question", "")).strip()[:1000],
                choices=json.dumps([str(c)[:200] for c in choices]),
                correct_index=correct_index,
                explanation=str(q.get("explanation", "")).strip()[:1000],
                source_topic=str(q.get("topic", topics[0])).strip()[:256],
            )
        )
    return rows[:5]


# ── Mastery roll-up + weak-topic scan ──────────────────────────────

async def record_attempt(
    db: AsyncSession, question: QuizQuestion, chosen_index: int
) -> QuizAttempt:
    is_correct = chosen_index == question.correct_index

    attempt = QuizAttempt(
        question_id=question.id,
        chosen_index=chosen_index,
        is_correct=is_correct,
    )
    db.add(attempt)
    await db.flush()

    # Roll up mastery for this topic.
    result = await db.execute(
        select(UserProgress).where(UserProgress.topic == question.source_topic)
    )
    row = result.scalar_one_or_none()
    now = datetime.now(UTC)
    if row is None:
        row = UserProgress(
            topic=question.source_topic,
            attempts=1,
            correct=1 if is_correct else 0,
            mastery=1.0 if is_correct else 0.0,
            last_seen_at=now,
        )
        db.add(row)
    else:
        row.attempts += 1
        if is_correct:
            row.correct += 1
        row.mastery = row.correct / row.attempts
        row.last_seen_at = now
    await db.commit()
    await db.refresh(attempt)
    await db.refresh(row)
    return attempt


async def weak_topics(db: AsyncSession, limit: int = 5) -> list[UserProgress]:
    """Topics with the lowest mastery, where the learner has actually tried."""
    result = await db.execute(
        select(UserProgress)
        .where(UserProgress.attempts > 0)
        .order_by(UserProgress.mastery.asc(), UserProgress.last_seen_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def recommendation(db: AsyncSession) -> str:
    """One-sentence study recommendation based on the weakest known topic."""
    weak = await weak_topics(db, limit=1)
    if not weak:
        return "No quiz attempts yet — try a quiz to build your topic mastery profile."
    mastery_pct = int(weak[0].mastery * 100)
    return (
        f"Focus on '{weak[0].topic}' next — current mastery {mastery_pct}% "
        f"({weak[0].correct}/{weak[0].attempts} correct)."
    )
