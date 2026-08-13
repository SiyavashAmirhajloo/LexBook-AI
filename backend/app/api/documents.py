"""Documents API: upload, list, delete, search."""
import os
import shutil
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, delete, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from app.core.db import get_db
from app.models import Document, DocumentChunk
from app.schemas.documents import DocumentResponse, SearchResponse, SearchResult
from app.services.document_processor import process_uploaded_pdf
from app.services.embeddings import get_embedding_provider

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")


@router.post("/documents/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF, extract text, chunk, embed, and store in pgvector."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Create upload directory
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Save to disk with UUID name to avoid collisions
    import uuid as uuid_module
    file_stem = Path(file.filename).stem
    save_name = f"{uuid_module.uuid4().hex}.pdf"
    file_path = str(Path(UPLOAD_DIR) / save_name)

    # Stream save (avoid reading whole file into memory)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process (extract, chunk, embed, store)
    try:
        doc = await process_uploaded_pdf(file_path, db, UPLOAD_DIR)
    except Exception as e:
        # Clean up file on failure
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        page_count=doc.page_count,
        upload_date=doc.upload_date,
    )


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    """List all uploaded documents."""
    result = await db.execute(select(Document).order_by(Document.upload_date.desc()))
    docs = result.scalars().all()
    return [
        DocumentResponse(
            id=d.id, title=d.title, page_count=d.page_count, upload_date=d.upload_date
        )
        for d in docs
    ]


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(document_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a document and its chunks, and remove the file from disk."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete chunks (cascade via FK)
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    await db.delete(doc)
    await db.commit()

    # Remove file from disk
    if doc.file_location:
        Path(doc.file_location).unlink(missing_ok=True)


@router.post("/documents/{document_id}/search", response_model=SearchResponse)
async def search_document(
    document_id: UUID,
    query: str,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Vector similarity search within a single document."""
    provider = get_embedding_provider()

    # Check document exists
    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Embed the query
    query_embedding = provider.embed(query)

    # Similarity search: cosine distance, order ascending, take top_k
    chunk_result = await db.execute(
        select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            DocumentChunk.page_number,
            DocumentChunk.text,
            DocumentChunk.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .where(DocumentChunk.document_id == document_id)
        .order_by("distance")
        .limit(top_k)
    )
    rows = chunk_result.all()

    results = []
    for row in rows:
        # cosine_distance in [0, 2]; similarity = 1 - distance/2
        similarity = 1 - (row.distance / 2)
        results.append(
            SearchResult(
                chunk_id=row.id,
                document_id=row.document_id,
                document_title=doc.title,
                page_number=row.page_number,
                text=row.text,
                score=similarity,
            )
        )

    return SearchResponse(query=query, results=results)