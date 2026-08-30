"""AI Study Planner service (V10) — the flagship.

A deterministic reasoning core (so every recommendation is explainable
and reproducible) with an optional LLM-written summary on top.

Inputs are all pre-existing version data:
- V3 study sessions        → what was studied recently
- V6 user_progress         → topic mastery / weaknesses
- V7 vocabulary memory     → words due for review (spaced repetition)
- V8 analytics estimation  → IELTS/TOEFL readiness

No new data sources, no new dependencies.
"""
from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import StudySession, UserProgress, Vocabulary
from app.services.analytics import compute_snapshot
from app.services.memory import weak_topics

# ── Spaced repetition ( Leitner-style, simple and explainable ) ────

# Intervals in days per review bucket. A word moves up on correct
# recall, down to bucket 0 on a miss. V6 quiz correctness per topic is
# our recall proxy for grammar topics; vocabulary uses seen_count.
SR_INTERVALS_DAYS = (1, 3, 7, 14, 30)


def _days_since(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    return max(0, (datetime.now(UTC) - dt).days)


def _due_words(vocab: list[Vocabulary], max_items: int = 5) -> list[dict[str, Any]]:
    """Words whose next review is due, oldest bucket first.

    Bucket heuristic: seen_count maps to interval index (capped). A word
    is due when days_since_last_seen >= interval[bucket].
    """
    due: list[dict[str, Any]] = []
    for v in vocab:
        bucket = min(v.seen_count - 1, len(SR_INTERVALS_DAYS) - 1)
        interval = SR_INTERVALS_DAYS[bucket]
        days = _days_since(v.last_seen_at)
        if days is None:
            continue
        if days >= interval:
            due.append(
                {
                    "word": v.word,
                    "topic": v.topic,
                    "bucket": bucket + 1,
                    "interval_days": interval,
                    "days_since_seen": days,
                    "reason": (
                        f"seen {days}d ago, review interval is {interval}d "
                        f"(bucket {bucket + 1})"
                    ),
                }
            )
    due.sort(key=lambda x: x["days_since_seen"], reverse=True)
    return due[:max_items]


# ── Skill focus decision ───────────────────────────────────────────

def _decide_skill_focus(
    weak: list[UserProgress], due: list[dict[str, Any]], recent_topics: list[str]
) -> tuple[str, str]:
    """Pick the next session's focus skill. Returns (skill, reason).

    Priority: weak grammar topic → due vocabulary → recent-topic
    continuation → default balanced reading.
    """
    if weak:
        w = weak[0]
        return (
            "grammar",
            f"Weakest topic '{w.topic}' at {int(w.mastery * 100)}% mastery "
            f"({w.correct}/{w.attempts} correct) — targeted grammar practice first.",
        )
    if due:
        return (
            "vocabulary",
            f"{len(due)} vocabulary item(s) overdue for spaced review "
            f"(e.g. '{due[0]['word']}', {due[0]['reason']}).",
        )
    if recent_topics:
        return (
            "reading",
            f"No weak topics or due reviews — continue momentum with reading "
            f"practice around '{recent_topics[0]}'.",
        )
    return (
        "reading",
        "Fresh start — no history yet. Begin with a reading passage to "
        "establish a baseline.",
    )


def _recommend_next_topic(
    weak: list[UserProgress], sessions: list[StudySession], due: list[dict[str, Any]]
) -> tuple[str, str]:
    """What topic to study next, with the reason."""
    if weak:
        w = weak[0]
        return (
            w.topic,
            f"Lowest mastery ({int(w.mastery * 100)}%, {w.attempts} attempt(s)) — "
            f"review and re-test this topic.",
        )
    # Continue from the most recent session's last topic
    if sessions and (sessions[0].topics or []):
        t = sessions[0].topics[-1]
        return (
            t,
            f"Continue where you left off — '{t}' was the last topic you "
            f"studied in your most recent session.",
        )
    return (
        "IELTS reading fundamentals",
        "No study history yet — start with the fundamentals.",
    )


# ── Readiness (reuses V8 transparent estimation) ───────────────────

def _readiness_summary(analytics: dict) -> dict[str, Any]:
    ielts = analytics["estimated_ielts"]
    toefl = analytics["estimated_toefl"]
    return {
        "ielts_band": ielts["value"],
        "toefl_score": toefl["value"],
        "weighted_mastery": ielts["inputs"]["weighted_mastery"],
        "note": (
            f"Same transparent formula as the dashboard: "
            f"quiz_mastery={ielts['inputs']['quiz_mastery']}, "
            f"coverage={ielts['inputs']['coverage']}, "
            f"completion={ielts['inputs']['completion']}."
        ),
    }


# ── LLM plan summary (optional; template fallback) ─────────────────

_PLAN_PROMPT = """You are an IELTS/TOEFL study coach writing a short daily plan.

Data:
- Focus skill today: {skill} ({skill_reason})
- Topic to study: {topic} ({topic_reason})
- Weak topics: {weak}
- Vocabulary due for review: {due}
- Readiness: IELTS band {ielts}, TOEFL {toefl}

Write a motivating 3-5 sentence plan in plain English addressed to the
learner. Mention the focus skill, the topic, and at least one due
vocabulary word if any. Be specific and encouraging. Return ONLY the
plan text, no JSON, no markdown.
"""


async def _llm_plan_summary(data: dict[str, Any]) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )
    prompt = _PLAN_PROMPT.format(
        skill=data["focus_skill"],
        skill_reason=data["focus_reason"],
        topic=data["recommended_topic"],
        topic_reason=data["topic_reason"],
        weak=", ".join(w["topic"] for w in data["weak_topics"]) or "none yet",
        due=", ".join(w["word"] for w in data["due_reviews"]) or "none",
        ielts=data["readiness"]["ielts_band"],
        toefl=data["readiness"]["toefl_score"],
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url, json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
            )
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass
    return None


def _template_plan_summary(data: dict[str, Any]) -> str:
    parts = [f"Today's focus: **{data['focus_skill']}** on '{data['recommended_topic']}'."]
    if data["due_reviews"]:
        words = ", ".join(f"'{w['word']}'" for w in data["due_reviews"][:3])
        parts.append(f"Review overdue vocabulary: {words}.")
    if data["weak_topics"]:
        w = data["weak_topics"][0]
        parts.append(
            f"Priority is '{w['topic']}' — mastery is only "
            f"{int(w['mastery'] * 100)}%."
        )
    parts.append(
        f"Current readiness: IELTS ~{data['readiness']['ielts_band']}, "
        f"TOEFL ~{data['readiness']['toefl_score']}."
    )
    return " ".join(parts)


# ── Main entry point ───────────────────────────────────────────────

async def build_todays_plan(db: AsyncSession) -> dict[str, Any]:
    """Build the full plan + reasoning. Fully explainable."""
    reasoning: list[str] = []

    # 1. Recent study history (V3)
    sessions = (
        await db.execute(
            select(StudySession).order_by(StudySession.started_at.desc()).limit(5)
        )
    ).scalars().all()
    recent_topics: list[str] = []
    for s in sessions:
        for t in s.topics or []:
            if t not in recent_topics:
                recent_topics.append(t)
    reasoning.append(
        f"Analyzed {len(sessions)} recent session(s) covering "
        f"{len(recent_topics)} distinct topic(s)."
    )

    # 2. Weakness memory (V6/V7)
    weak = await weak_topics(db, min_attempts=1, mastery_ceiling=0.5, limit=5)
    weak_list = [
        {"topic": w.topic, "mastery": round(w.mastery, 2), "attempts": w.attempts,
         "correct": w.correct}
        for w in weak
    ]
    reasoning.append(
        f"Weakness memory: {len(weak_list)} topic(s) below 50% mastery."
        if weak_list
        else "Weakness memory: nothing below 50% mastery (or no quiz attempts yet)."
    )

    # 3. Vocabulary due for review (V7 + spaced repetition)
    vocab = (
        await db.execute(select(Vocabulary).order_by(Vocabulary.last_seen_at.desc()))
    ).scalars().all()
    due = _due_words(list(vocab))
    reasoning.append(
        f"Spaced repetition: {len(due)} word(s) due for review out of "
        f"{len(vocab)} tracked (Leitner intervals 1/3/7/14/30 days)."
    )

    # 4. Readiness (V8 estimation)
    analytics = await compute_snapshot(db)
    readiness = _readiness_summary(analytics)
    reasoning.append(
        f"Readiness computed from V8 formula: weighted_mastery="
        f"{readiness['weighted_mastery']}."
    )

    # 5. Decisions
    focus_skill, focus_reason = _decide_skill_focus(weak, due, recent_topics)
    recommended_topic, topic_reason = _recommend_next_topic(weak, list(sessions), due)
    reasoning.append(f"Focus skill decision: {focus_skill} — {focus_reason}")
    reasoning.append(f"Topic decision: {recommended_topic} — {topic_reason}")

    # Next-chapter suggestion: use V1 pgvector retrieval on the recommended
    # topic to point at the book pages that cover it.
    next_chapter = None
    try:
        from app.services.study_sessions import resolve_studied_section

        resolved = await resolve_studied_section(db, recommended_topic, top_k=3)
        if resolved["document_id"] and resolved["page_start"]:
            next_chapter = {
                "document_title": resolved["document_title"],
                "pages": [resolved["page_start"], resolved["page_end"]],
                "reason": "Book section matching the recommended topic.",
            }
            reasoning.append(
                f"Next chapter: pages {resolved['page_start']}–{resolved['page_end']} "
                f"of '{resolved['document_title']}' match the topic."
            )
    except Exception:
        reasoning.append("Next chapter: no matching book section found.")

    data: dict[str, Any] = {
        "focus_skill": focus_skill,
        "focus_reason": focus_reason,
        "recommended_topic": recommended_topic,
        "topic_reason": topic_reason,
        "weak_topics": weak_list,
        "due_reviews": due,
        "next_chapter": next_chapter,
        "readiness": readiness,
        "recent_topics": recent_topics[:8],
        "reasoning": reasoning,
    }

    # 6. LLM narrative (fallback: template)
    llm = await _llm_plan_summary(data)
    data["summary"] = llm or _template_plan_summary(data)
    data["summary_source"] = "llm" if llm else "template"
    reasoning.append(f"Narrative: {data['summary_source']}.")

    return data
