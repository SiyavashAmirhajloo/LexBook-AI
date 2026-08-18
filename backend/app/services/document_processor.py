"""Process uploaded documents: extract, chunk, embed, store."""
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, DocumentChunk
from app.services.embeddings import get_embedding_provider
from app.services.pdf import extract_metadata, extract_text_from_pdf


async def process_uploaded_pdf(
    file_path: str, db: AsyncSession, upload_dir: str
) -> Document:
    """Process a newly uploaded PDF: extract metadata, chunk, embed, store in DB."""
    provider = get_embedding_provider()

    metadata = extract_metadata(file_path)

    doc_record = Document(
        title=metadata["title"],
        file_location=file_path,
        page_count=metadata["page_count"],
        upload_date=datetime.now(UTC),
    )
    db.add(doc_record)
    await db.flush()  # assign ID without committing transaction

    chunks_data, total_pages = extract_text_from_pdf(file_path)
    chunk_texts = [cd["text"] for cd in chunks_data]

    if chunk_texts:
        embeddings = provider.embed_batch(chunk_texts)
    else:
        embeddings = []

    for idx, (chunk_data, embedding) in enumerate(zip(chunks_data, embeddings, strict=False)):
        if not chunk_data["text"].strip():
            continue

        chunk_record = DocumentChunk(
            document_id=doc_record.id,
            page_number=int(chunk_data["page"]) if str(chunk_data["page"]).isdigit() else 1,
            chunk_index=idx,
            text=chunk_data["text"].strip(),
            embedding=embedding,
        )
        db.add(chunk_record)

    doc_record.page_count = total_pages
    await db.commit()
    await db.refresh(doc_record)

    return doc_record
