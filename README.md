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
- **Hybrid search** – BM25 + vector reranking (Version 4).
- **Web Intelligence** – search the internet for learning resources (Version 5).
- **Personalization** – flashcards, spaced repetition, weak-topic detection (Version 6).
- **Long-Term Memory** – persist everything across sessions (Version 7).
- **Authentication** – OAuth login + guest mode (Version 9).
- **Production hardening** – logging, monitoring, production Nginx setup.

---

## Version 2 – Semantic Chat

**Goal:** Let users talk with their books and get cited answers.

- **LLM abstraction layer** – `app/services/llm.py` with a `GeminiProvider` (Gemini 1.5 Flash via REST SSE). Swappable via `LLM_PROVIDER` env. Falls back gracefully if `GEMINI_API_KEY` is missing.
- **Streaming chat** – `POST /api/v1/chat` streams token-by-token via SSE (`data: {"type":"token","content":"..."}`). Final event delivers citations (`{"type":"citations","citations":[...]}`).
- **Citations** – every answer cites numbered sources from the vector search, showing document title + page number + similarity score. Click a citation to expand the full excerpt.
- **Conversation history** – messages are persisted to the DB (`conversations` + `messages` tables). Resume any past session from the history list.
- **Chat UI** – `/chat` page with streaming tokens rendered in real time, citation chips under each assistant message, and a click-to-expand excerpt view.

### API Endpoints (new in V2)
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/chat` | Streaming chat (SSE tokens + final citations) |
| `GET` | `/api/v1/conversations` | List all chat conversations |
| `GET` | `/api/v1/conversations/{id}/messages` | Get full message history for a conversation |

### Usage Demo
1. Upload a PDF via `/library` (or via `POST /api/v1/documents/upload`).
2. Open `/chat` and type a question (e.g. "Explain present perfect with examples").
3. Watch the answer stream in token-by-token; numbered source chips appear below.
4. Click a citation chip to see the full excerpt from the original book.

### What's Still Missing (future versions)
- **Hybrid search** – BM25 + vector reranking (Version 4).
- **Web Intelligence** – search the internet for learning resources (Version 5).
- **Personalization** – flashcards, spaced repetition, weak-topic detection (Version 6).
- **Long-Term Memory** – persist everything across sessions (Version 7).
- **Authentication** – OAuth login + guest mode (Version 9).
- **Production hardening** – logging, monitoring, production Nginx setup.

---

## Version 3 – Study Sessions

**Goal:** Give the system awareness of what the user is actually studying, not just what they ask about.

- **Study session model** – `study_sessions` table records the raw input, the resolved book, the page range, extracted topics/keywords, a summary, and start/finish timestamps.
- **Natural-language section matching** – say "I finished Unit 7" or "I studied Relative Clauses" and the system embeds that phrase and runs the same pgvector cosine search from V1/V2 to locate the matching chunks. No second retrieval system.
- **Topic extraction** – the matched chunk text is sent to Gemini with a pedagogical prompt that returns structured JSON: `topics` (e.g. "Passive Voice", "CARS Model"), `keywords` (key terms to remember), and a plain-English `summary`.
- **Offline fallback** – if `GEMINI_API_KEY` is absent or the call fails, a frequency-based heuristic still produces keywords so the pipeline never breaks.
- **Session history** – every session persists so Versions 6–10 (personalization, memory, study planner) can build on it.
- **Study Sessions UI** – `/study-sessions` page: start a session, optionally pin it to a specific book, see extraction results immediately, and browse past sessions with their topic/keyword chips.

### API Endpoints (new in V3)
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/study-sessions/start` | Resolve what was studied + extract topics/keywords |
| `POST` | `/api/v1/study-sessions/{id}/finish` | Mark a session complete |
| `GET` | `/api/v1/study-sessions` | List session history with extracted topics |

### Usage Demo
1. Upload a book via `/library`.
2. Open `/study-sessions` and type what you studied, e.g. "I finished the section on Relative Clauses".
3. The system finds the matching pages, then shows extracted topics, keywords, and a summary.
4. Click **Mark Finished** to close the session; it stays in the history list.

### What's Still Missing (future versions)
- **Agent orchestration** – LangGraph multi-agent workflow (Version 4).
- **Web Intelligence** – search the internet for learning resources (Version 5).
- **Personalization** – flashcards, spaced repetition, weak-topic detection (Version 6).
- **Long-Term Memory** – persist everything across sessions (Version 7).
- **Authentication** – OAuth login + guest mode (Version 9).
- **AI Study Planner** – proactive daily study planning (Version 10).

---

## Version 4 – Agentic Workflow

**Goal:** Replace ad-hoc chat/extraction logic with a real LangGraph orchestration layer that later versions plug into.

- **LangGraph graph** – `app/agents/graph.py` compiles `coordinator → planner → {rag | study} → memory → evaluation` with a conditional edge on the planner's decision.
- **Coordinator** – single entry point for every request; records the incoming intent and hands off to the planner.
- **Planner** – picks the agent plan. An explicit `intent` from the API wins; otherwise it infers from the message text (keyword-based for now; an LLM planner can replace it without touching the graph).
- **RAG Agent** – wraps the V2 retrieve-then-generate path. Retrieval still runs in the service layer so the SSE streaming contract is unchanged.
- **Study Agent** – wraps the V3 session/topic-extraction path.
- **Memory Agent (stub)** – round-trips a per-request fact list through graph state. Real long-term memory is V7; this is the interface/plumbing only.
- **Evaluation Agent (stub)** – emits a groundedness estimate per request. Full RAG metrics, hallucination detection, and citation accuracy come later.
- **Tracing** – every node appends to `state["trace"]`, and both endpoints log the full trace plus an `[eval]` summary line, so graph behavior is inspectable from `docker logs`.

### Example trace (chat request)
```
[graph] intent=chat traced=5 route=rag
[graph]   coordinator: intent='chat' -> planner
[graph]   planner: intent='chat' plan=['rag'] route='rag'
[graph]   rag_agent: passthrough (context already retrieved upstream)
[graph]   memory_agent: new=0 recalled=0 total=0
[graph]   evaluation_agent: grounded=True
[eval] intent=chat route=rag grounded=True context_chunks=6
```

### Example trace (study session)
```
[graph] intent=study traced=5 route=study
[graph]   coordinator: intent='study' -> planner
[graph]   planner: intent='study' plan=['study'] route='study'
[graph]   study_agent: study_result = True
[graph]   memory_agent: new=0 recalled=0 total=0
[graph]   evaluation_agent: grounded=True
[eval] intent=study route=study grounded=True context_chunks=0
```

### Fully implemented vs. stubbed
| Agent | Status |
|-------|--------|
| Coordinator | Implemented (intent capture + handoff) |
| Planner | Minimal — keyword/intent routing, no LLM planning yet |
| RAG Agent | Implemented (wraps V2 retrieval + generation) |
| Study Agent | Implemented (wraps V3 extraction) |
| Memory Agent | **Stub** — state plumbing only, real memory in V7 |
| Evaluation Agent | **Stub** — logs groundedness, full metrics later |

### What's Still Missing (future versions)
- **Web Intelligence** – search the internet for learning resources (Version 5).
- **Personalization** – flashcards, spaced repetition, weak-topic detection (Version 6).
- **Long-Term Memory** – persist everything across sessions (Version 7).
- **Authentication** – OAuth login + guest mode (Version 9).
- **AI Study Planner** – proactive daily study planning (Version 10).

---

## Remaining Docs
- See `docs/roadmap.md` for the full version roadmap.
- The `frontend/` and `backend/` directories each contain their own developer instructions.
- See `.env.example` for environment variable reference.

*Built with the mandated tech stack: FastAPI, SQLAlchemy, Alembic, PostgreSQL + pgvector, Next.js + TypeScript + Tailwind, Docker, GitHub Actions.*
