"""PDF processing: extraction, chunking, metadata."""
import os
from pathlib import Path

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_text_from_pdf(pdf_path: str) -> tuple[list[dict], int]:
    """
    Extract text from PDF, returning list of chunk dicts with page_number + text.

    Strategy:
    - Extract text page-by-page
    - Chunk per-page with RecursiveCharacterTextSplitter (preserves page context)
    - chunk_size=800, overlap=100, separators prioritize paragraphs > lines > sentences
    - Returns [{"page": int, "text": str}, ...] + total page count
    """
    doc = fitz.open(pdf_path)
    all_chunks: list[dict] = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()
        if not text:
            continue

        chunks = splitter.split_text(text)
        for chunk in chunks:
            all_chunks.append({
                "page": page_num + 1,
                "text": chunk.strip(),
            })

    return all_chunks, len(doc)


def extract_metadata(pdf_path: str) -> dict:
    """Extract basic metadata from PDF."""
    doc = fitz.open(pdf_path)
    metadata = {"file_path": pdf_path}

    doc_info = doc.metadata
    if doc_info and doc_info.get("title"):
        metadata["title"] = doc_info["title"]
    else:
        metadata["title"] = Path(pdf_path).stem

    metadata["page_count"] = len(doc)
    metadata["file_size"] = os.path.getsize(pdf_path)

    if doc_info and doc_info.get("author"):
        metadata["author"] = doc_info["author"]

    return metadata
