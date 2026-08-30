"""Analytics service for V8.

Pulls every metric from the V2/V3/V6/V7 data we already have — no
parallel tracking. Estimates are intentionally transparent (formula +
inputs returned in the response) so the dashboard can render them as
explanations, not black-box numbers.

Estimation method (visible to the user):

  - weighted_mastery = 0.5 * quiz_mastery      # V6 user_progress
                   + 0.3 * coverage              # topics studied / max(1, distinct topics)
                   + 0.2 * completion            # finished sessions / max(1, total sessions)

  - ielts_band (1.0..9.0, half-step)  = 4.5 + 4.0 * weighted_mastery
  - toefl_score (0..120)             = 30 + 90 * weighted_mastery

The same `weighted_mastery` feeds both, so a single view explains both
predictions.
"""
from collections import Counter
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Document,
    LongTermFact,
    QuizAttempt,
    QuizQuestion,
    StudySession,
    UserProgress,
    Vocabulary,
)

SCORING_METHOD = (
    "weighted_mastery = 0.5*quiz_mastery + 0.3*coverage + 0.2*completion. "
    "ielts_band = 4.5 + 4.0*weighted_mastery. "
    "toefl_score = 30 + 90*weighted_mastery. "
    "coverage = distinct_topics_studied / max(1, max_distinct_topics). "
    "completion = finished_sessions / max(1, total_sessions)."
)


def _date(dt: datetime) -> str:
    return dt.date().isoformat()


async def compute_snapshot(db: AsyncSession) -> dict:
    # ── Totals ────────────────────────────────────────────────
    books_n = (await db.execute(select(func.count(Document.id)))).scalar_one()
    sessions_total = (await db.execute(select(func.count(StudySession.id)))).scalar_one()
    sessions_finished = (
        await db.execute(
            select(func.count(StudySession.id)).where(StudySession.finished_at.is_not(None))
        )
    ).scalar_one()
    sessions = (
        await db.execute(select(StudySession).order_by(StudySession.started_at.asc()))
    ).scalars().all()
    facts_n = (await db.execute(select(func.count(LongTermFact.id)))).scalar_one()
    vocab_n = (await db.execute(select(func.count(Vocabulary.id)))).scalar_one()
    quiz_attempts = (await db.execute(select(func.count(QuizAttempt.id)))).scalar_one()
    quiz_correct = (
        await db.execute(select(func.count(QuizAttempt.id)).where(QuizAttempt.is_correct.is_(True)))
    ).scalar_one()

    # Pages studied: for every session, estimate from page range
    pages_studied = 0
    minutes_studied = 0
    for s in sessions:
        if s.page_start and s.page_end and s.page_end >= s.page_start:
            pages_studied += s.page_end - s.page_start + 1
        if s.finished_at and s.started_at:
            minutes_studied += int(
                max(0, (s.finished_at - s.started_at).total_seconds()) / 60
            )

    # ── Study time (sessions per day) ─────────────────────────
    daily = Counter()
    for s in sessions:
        daily[_date(s.started_at)] += 1
    study_time = [
        {"date": d, "value": float(c)} for d, c in sorted(daily.items())
    ]

    # ── Vocabulary growth (running total) ─────────────────────
    vocab_events = []
    vocab_rows = (
        await db.execute(select(Vocabulary).order_by(Vocabulary.last_seen_at.asc()))
    ).scalars().all()
    for v in vocab_rows:
        vocab_events.append(_date(v.last_seen_at))
    growth = sorted(Counter(vocab_events).items())
    running = 0
    vocab_growth = []
    for d, n in growth:
        running += n
        vocab_growth.append({"date": d, "value": float(running)})

    # ── Learning curve (daily quiz accuracy) ───────────────────
    attempt_rows = (
        await db.execute(
            select(QuizAttempt, QuizQuestion)
            .join(QuizQuestion, QuizAttempt.question_id == QuizQuestion.id)
            .order_by(QuizAttempt.created_at.asc())
        )
    ).all()
    by_day_correct: Counter = Counter()
    by_day_total: Counter = Counter()
    for attempt, _q in attempt_rows:
        d = _date(attempt.created_at)
        by_day_total[d] += 1
        if attempt.is_correct:
            by_day_correct[d] += 1
    curve = []
    for d in sorted(set(by_day_total) | set(by_day_correct)):
        t = by_day_total[d]
        c = by_day_correct[d]
        curve.append({"date": d, "value": round(c / t, 3) if t else 0.0})

    # ── Grammar topics & mistakes ─────────────────────────────
    progress_rows = (await db.execute(select(UserProgress))).scalars().all()
    grammar_topics = [
        {
            "topic": p.topic,
            "mastery": round(p.mastery, 3),
            "attempts": p.attempts,
            "correct": p.correct,
        }
        for p in progress_rows
    ]
    mistakes = [
        g for g in grammar_topics if g["attempts"] >= 1 and g["mastery"] < 0.5
    ]
    weak_topic_count = len(mistakes)

    # ── Knowledge graph (topic co-occurrence) ──────────────────
    co: Counter = Counter()
    topic_freq: Counter = Counter()
    for s in sessions:
        topics = list(dict.fromkeys(s.topics or []))  # dedupe, preserve order
        for t in topics:
            topic_freq[t] += 1
        for i in range(len(topics)):
            for j in range(i + 1, len(topics)):
                pair = tuple(sorted((topics[i], topics[j])))
                co[pair] += 1

    # weight normalization: max appearance in 0..1 for node size
    max_freq = max(topic_freq.values(), default=1)
    nodes = [
        {"id": t, "label": t, "weight": round(c / max_freq, 3)}
        for t, c in topic_freq.most_common(40)
    ]
    edges = [
        {"source": a, "target": b, "weight": c}
        for (a, b), c in co.most_common(120)
        if c > 0
    ]

    # ── Timeline (recent sessions, newest first) ────────────────
    timeline = [
        {
            "id": str(s.id),
            "started_at": s.started_at,
            "finished_at": s.finished_at,
            "raw_input": s.raw_input,
            "topics": s.topics or [],
        }
        for s in sorted(sessions, key=lambda x: x.started_at, reverse=True)[:20]
    ]

    # ── Estimates (transparent) ───────────────────────────────
    quiz_mastery = (
        sum(p.mastery * p.attempts for p in progress_rows) /
        max(1, sum(p.attempts for p in progress_rows))
    )
    distinct_topics_studied = sum(1 for s in sessions if (s.topics or []))
    max_distinct_topics = max(
        (len(s.topics or []) for s in sessions), default=0
    )
    coverage = (
        distinct_topics_studied / max(1, max_distinct_topics)
        if max_distinct_topics else 0.0
    )
    completion = (
        sessions_finished / max(1, sessions_total) if sessions_total else 0.0
    )
    weighted = 0.5 * quiz_mastery + 0.3 * coverage + 0.2 * completion
    weighted = min(1.0, max(0.0, weighted))

    ielts_band = 4.5 + 4.0 * weighted
    # round to nearest 0.5
    ielts_band = round(ielts_band * 2) / 2
    toefl_score = 30 + 90 * weighted

    return {
        "totals": {
            "books_uploaded": books_n,
            "pages_studied": pages_studied,
            "sessions_count": sessions_total,
            "sessions_finished": sessions_finished,
            "vocabulary_count": vocab_n,
            "facts_count": facts_n,
            "quiz_attempts": quiz_attempts,
            "quizzes_correct": quiz_correct,
            "weak_topic_count": weak_topic_count,
            "minutes_studied": minutes_studied,
        },
        "study_time": study_time,
        "vocabulary_growth": vocab_growth,
        "learning_curve": curve,
        "grammar_topics": grammar_topics,
        "mistakes": mistakes,
        "knowledge_graph": {"nodes": nodes, "edges": edges},
        "timeline": timeline,
        "estimated_ielts": {
            "label": "Estimated IELTS band",
            "value": ielts_band,
            "scale": "1.0 - 9.0 (half-step)",
            "method": SCORING_METHOD,
            "inputs": {
                "weighted_mastery": round(weighted, 3),
                "quiz_mastery": round(quiz_mastery, 3),
                "coverage": round(coverage, 3),
                "completion": round(completion, 3),
            },
        },
        "estimated_toefl": {
            "label": "Estimated TOEFL score",
            "value": round(toefl_score),
            "scale": "0 - 120",
            "method": SCORING_METHOD,
            "inputs": {
                "weighted_mastery": round(weighted, 3),
                "quiz_mastery": round(quiz_mastery, 3),
                "coverage": round(coverage, 3),
                "completion": round(completion, 3),
            },
        },
        "scoring_method": SCORING_METHOD,
    }
