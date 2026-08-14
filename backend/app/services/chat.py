"""Retrieve-then-generate chat service (V2).

Straightforward RAG: embed the question, pull top-k chunks via pgvector,
build a grounded prompt with numbered sources, and return the prompt +
citation metadata. No agents — that starts in V4.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, DocumentChunk
from app.services.embeddings import get_embedding_provider

SYSTEM_PROMPT = """You are LexBook AI, a study companion for English learners \
preparing for IELTS and TOEFL.

Answer the user's question using ONLY the numbered sources provided below.
Rules:
- Cite sources inline using [1], [2], etc. matching the source numbers.
- If several sources support a point, cite all of them, e.g. [1][3].
- If the sources do not contain the answer, say so plainly instead of guessing.
- Be concise and pedagogical: explain the concept, then give an example.
"""


async def retrieve_context(
    db: AsyncSession,
    question: str,
    document_id: UUID | None = None,
    top_k: int = 6,
) -> tuple[str, list[dict]]:
    """Retrieve relevant chunks and build a grounded prompt block.

    Returns (context_block, citations). Citations carry the metadata the
    frontend needs to render a clickable source with its excerpt.
    """
    provider = get_embedding_provider()
    query_embedding = provider.embed(question)

    stmt = (
        select(
            DocumentChunk.id,
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

    citations: list[dict] = []
    blocks: list[str] = []

    for i, row in enumerate(rows, start=1):
        citations.append(
            {
                "index": i,
                "chunk_id": str(row.id),
                "document_id": str(row.document_id),
                "document_title": row.title,
                "page_number": row.page_number,
                "excerpt": row.text,
                "score": 1 - (row.distance / 2),
            }
        )
        blocks.append(f"[{i}] {row.title}, p. {row.page_number}\n{row.text}")

    context_block = "\n\n".join(blocks) if blocks else "(no sources found)"
    return context_block, citations


def build_user_prompt(question: str, context_block: str) -> str:
    """Compose the final user-facing prompt sent to the LLM."""
    return f"Sources:\n{context_block}\n\nQuestion: {question}"