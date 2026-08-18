"""Study session services (V3): resolve what was studied, extract topics.

Reuses the V1/V2 embedding + pgvector retrieval rather than building a
second retrieval path.
"""
import json
import os
import re
from collections import Counter
from uuid import UUID  # noqa: F401

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, DocumentChunk
from app.services.embeddings import get_embedding_provider

EXTRACTION_PROMPT = """You are an expert English teacher analysing what a student just studied.

Return ONLY valid JSON (no markdown fences, no prose) with these keys:
- "topics": 1-6 pedagogical topic names, e.g. "Relative Clauses", "Passive Voice",
  "Present Perfect", "Conditionals", "Modal Verbs", "IELTS Writing Task 2".
- "keywords": 5-12 key terms or short phrases the student should remember.
- "summary": one or two sentences of plain English summarising the section.

Studied text:
{content}
"""

STOPWORDS = set(
    "the a an and or but if is are was were be been being to of in on at for with by from as "
    "this that these those it its you your we they he she not no can will would should could "
    "have has had do does did there their them then than when what which who whom whose how".split()
)


async def resolve_studied_section(
    db: AsyncSession, raw_input: str, document_id: UUID | None = None, top_k: int = 8
) -> dict:
    """Match free-text input like "I finished Unit 7" to actual book chunks.

    Uses the same embedding + cosine search as V1/V2. Returns the matched
    document, page range, and the chunk texts that will feed extraction.
    """
    provider = get_embedding_provider()
    query_embedding = provider.embed(raw_input)

    stmt = (
        select(
            DocumentChunk.document_id,
            DocumentChunk.page_number,
            DocumentChunk.text,
            Document.title,
            DocumentChunk.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .order_by("distance")
        .limit(top_k)
    )
    if document_id is not None:
        stmt = stmt.where(DocumentChunk.document_id == document_id)

    rows = (await db.execute(stmt)).all()
    if not rows:
        return {"document_id": None, "document_title": None, "page_start": None, "page_end": None, "texts": []}

    pages = [r.page_number for r in rows]
    return {
        "document_id": rows[0].document_id,
        "document_title": rows[0].title,
        "page_start": min(pages),
        "page_end": max(pages),
        "texts": [r.text for r in rows],
    }


def _heuristic_extract(texts: list[str]) -> dict:
    """Offline fallback: most frequent distinctive words become keywords."""
    words = []
    for t in texts:
        words.extend(
            w for w in re.findall(r"[a-zA-Z']+", t.lower()) if w not in STOPWORDS and len(w) > 3
        )
    return {
        "topics": [],
        "keywords": [w for w, _ in Counter(words).most_common(10)],
        "summary": None,
    }


async def extract_topics(texts: list[str]) -> dict:
    """Extract topics/keywords/summary from studied text via Gemini, else heuristics."""
    if not texts:
        return {"topics": [], "keywords": [], "summary": None}

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _heuristic_extract(texts)

    model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = EXTRACTION_PROMPT.format(content="\n\n".join(texts)[:8000])

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                url, json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
            )
            resp.raise_for_status()
            raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Models often wrap JSON in ``` fences despite instructions.
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
        parsed = json.loads(raw)
        return {
            "topics": parsed.get("topics", []),
            "keywords": parsed.get("keywords", []),
            "summary": parsed.get("summary"),
        }
    except Exception:
        return _heuristic_extract(texts)