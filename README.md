# LexBook AI

**LexBook AI** is an AI‑powered personal learning platform built to help you study English and prepare for IELTS/TOEFL exams. It imports your PDF study materials, extracts the text, builds embeddings, and then surfaces personalized practice questions and resources.

## Quick Start (Docker)

```bash
# Clone the repo and cd into it
git clone <repo-url>
cd "LexBook AI"

# Build and start all services
docker compose up --build
```

- **Frontend UI**: <http://localhost:3000> — opens the Library page directly.
- **Backend API**: <http://localhost:8000/api/v1/health> — API health check.

---

## Version 0 – Project Foundation

- **Backend** – FastAPI (Python 3.13+) with async SQLAlchemy, Alembic migrations, health‑check endpoint.
- **Frontend** – Next.js (React + TypeScript) with TailwindCSS, dark‑mode capable shell page that calls the backend health endpoint.
- **Database** – PostgreSQL with the pgvector extension (via Docker Compose).
- **Containerisation** – Docker + Docker Compose for backend, frontend, and DB.
- **CI** – GitHub Actions lint, test and build for both services.

---

## Version 1 – Smart PDF Library

**Goal:** Turn the skeleton into a working local knowledge base.

- **PDF upload** – `POST /api/v1/documents/upload` stores PDFs locally and creates a DB entry.
- **Text extraction & chunking** – PyMuPDF extracts pages; `RecursiveCharacterTextSplitter` creates ~800-char chunks with 100-char overlap.
- **Embeddings** – 1024-dim vectors from **BAAI/bge-m3** (local via `fastembed`). Set `EMBEDDING_PROVIDER=hash` for an offline deterministic fallback.
- **Storage** – Chunks and embeddings saved in PostgreSQL/pgvector tables.
- **Search** – `POST /api/v1/documents/{id}/search` runs cosine similarity against a document's chunks, returning top-k matches.
- **Library UI** – `/library` page lets you upload PDFs, view existing books, delete them, and run semantic searches.

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Service health check |
| `POST` | `/api/v1/documents/upload` | Upload a PDF, extract text, chunk, embed, store |
| `GET` | `/api/v1/documents` | List all uploaded documents |
| `DELETE` | `/api/v1/documents/{id}` | Delete a document and its chunks |
| `POST` | `/api/v1/documents/{id}/search?query=...&top_k=5` | Vector similarity search |

### Usage Demo
1. Open the app (`http://localhost:3000`).
2. Click **Upload Study Book**, choose a PDF.
3. After processing (a few seconds), the book appears in the library list.
4. Click **Search Book**, type a query (e.g., "present perfect"), and view the top matching chunks with similarity scores.

### What's Still Missing (future versions)
- **Chat** – conversational Q&A over the knowledge base (Version 2).
- **Hybrid search** – BM25 + vector reranking (Version 4).
- **Web Intelligence** – search the internet for learning resources (Version 5).
- **Personalization** – flashcards, spaced repetition, weak-topic detection (Version 6).
- **Long-Term Memory** – persist everything across sessions (Version 7).
- **Authentication** – OAuth login + guest mode (Version 9).
- **Production hardening** – logging, monitoring, production Nginx setup.

---

## Remaining Docs
- See `docs/roadmap.md` for the full version roadmap.
- The `frontend/` and `backend/` directories each contain their own developer instructions.
- See `.env.example` for environment variable reference.