# LexBook AI

An AI-powered personal learning platform that turns static study materials into an
interactive, agentic learning experience. The first domain is **IELTS/TOEFL
preparation**, but the architecture is designed so any subject can plug in.

LexBook AI goes beyond "chat with your PDF": it understands what you are currently
studying, extracts the topics you covered, searches the web for reputable practice
material tied to those topics, and generates original practice questions — all
orchestrated through a LangGraph multi-agent workflow.

## Architecture at a Glance

```
PDF Library ──► pgvector (chunks + embeddings) ──► Semantic Chat with citations
                                                        │
Study Sessions ──► Topic/Keyword Extraction ────────────┤
        │                                               ▼
        └──────────► Internet Intelligence ◄──── LangGraph Agent Workflow
                     (curated web resources,      coordinator → planner →
                      original AI summaries +      {rag | study | internet}
                      generated questions)         → memory → evaluation
```

**Stack:** FastAPI (async) · PostgreSQL + pgvector · LangGraph · Gemini ·
fastembed · Next.js 15 + TypeScript + TailwindCSS · Docker Compose · GitHub Actions

## Quick Start

```bash
git clone https://github.com/SiyavashAmirhajloo/LexBook-AI.git
cd LexBook-AI

cp .env.example .env          # add your GEMINI_API_KEY
docker compose up --build -d
```

- **Frontend UI**: <http://localhost:3000>
- **Backend API**: <http://localhost:8000/api/v1/health>
- **Interactive API docs**: <http://localhost:8000/docs>

Migrations run automatically on container start. See `.env.example` for all
supported configuration (`EMBEDDING_PROVIDER`, `SEARCH_PROVIDER`,
`LLM_PROVIDER`, …).

## Feature Walkthrough

1. **Upload books** in `/library` — text is extracted, chunked, embedded into pgvector.
2. **Chat with your books** in `/chat` — streaming answers with clickable page-level citations.
3. **Log a study session** in `/study-sessions` — say *"I finished Unit 7"*; the system resolves the book section and extracts topics/keywords.
4. **Find web resources** on any session card — curated IELTS/TOEFL links ranked by source reputation, each with an original AI-written summary and generated practice questions.

---

## Version History

### V5 — Internet Intelligence *(current)*

Curated web resources tied to what you studied.

- **Search abstraction layer** — `SearchProvider` interface with a keyless
  DuckDuckGo provider; Tavily/Brave/SerpAPI drop in as single subclasses via
  `SEARCH_PROVIDER`.
- **Internet Agent** — new route in the agent graph; converts extracted session
  topics into targeted IELTS/TOEFL queries.
- **Reputable-source ranking** — official (ETS, British Council, IDP) →
  educational (Magoosh, IELTS Liz, E2Language…) → secondary (YouTube, Reddit),
  per `docs/architecture.md`.
- **Copyright-safe by construction** — search snippets are transient LLM input
  only. Persisted data: link, title, domain, an *original* AI-written summary,
  skill type, and AI-*generated* original practice questions. Verified by a
  sentinel test that fails if any snippet text reaches persistence.
- Graceful degradation to links-only when no LLM is reachable.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/study-sessions/{id}/resources` | Search + curate resources for the session's topics |
| `GET` | `/api/v1/study-sessions/{id}/resources` | List previously curated resources |

### V4 — Agentic Workflow

LangGraph multi-agent orchestration layer.

- Graph: `coordinator → planner → {rag | study | internet} → memory → evaluation`
- **Planner** routes each request; explicit intents win, otherwise keyword inference.
- Every node appends structured trace lines — inspectable via `docker logs`.
- Memory and Evaluation agents are interface-complete stubs (full functionality: V7+).

<details>
<summary>Example trace</summary>

```
[graph] intent=chat traced=5 route=rag
[graph]   coordinator: intent='chat' -> planner
[graph]   planner: intent='chat' plan=['rag'] route='rag'
[graph]   rag_agent: passthrough (context already retrieved upstream)
[graph]   memory_agent: new=0 recalled=0 total=0
[graph]   evaluation_agent: grounded=True
[eval] intent=chat route=rag grounded=True context_chunks=6
```
</details>

### V3 — Study Sessions

The system learns *what* you study, not just what you ask.

- Natural-language matching: *"I finished Unit 7 of English Grammar in Use"* →
  resolved book + page range, using the same pgvector retrieval (no second system).
- Gemini-driven extraction returns pedagogical `topics` ("Passive Voice",
  "CARS Model"), `keywords`, and a plain-English summary; frequency-based
  heuristic fallback keeps the pipeline alive without an LLM.
- Session history persists as the foundation for personalization (V6), memory
  (V7), and the AI Study Planner (V10).

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/study-sessions/start` | Resolve what was studied + extract topics/keywords |
| `POST` | `/api/v1/study-sessions/{id}/finish` | Mark a session complete |
| `GET` | `/api/v1/study-sessions` | Session history with extracted topics |

### V2 — Semantic Chat

Talk to your books; every answer is grounded and cited.

- Streaming SSE responses (`token` events → final `citations` payload).
- Numbered citations with document title, page number, similarity score, and
  click-to-expand excerpts.
- Provider-agnostic LLM layer (`LLM_PROVIDER`); conversation history persists
  across sessions.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/chat` | Streaming chat (SSE tokens + final citations) |
| `GET` | `/api/v1/conversations` | List conversations |
| `GET` | `/api/v1/conversations/{id}/messages` | Full message history |

### V1 — Smart PDF Library

Local knowledge base from your own materials.

- PDF upload → PyMuPDF extraction → recursive-character chunking (~800 chars,
  100 overlap, per-page) → 1024-dim embeddings → pgvector storage.
- Embedding abstraction layer (`EMBEDDING_PROVIDER`) with local fastembed
  default and offline deterministic fallback.
- Per-book vector similarity search.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload + process a PDF |
| `GET` / `DELETE` | `/api/v1/documents[/{id}]` | List / delete documents |
| `POST` | `/api/v1/documents/{id}/search?query=...&top_k=5` | Vector similarity search |

### V0 — Project Foundation

Async FastAPI backend with clean layering (API / services / core / models),
Next.js shell, PostgreSQL + pgvector via Docker Compose, Alembic migrations,
GitHub Actions CI for lint/test/build.

## Roadmap

| Version | Feature | Status |
|---------|---------|--------|
| V6 | Personalized learning — flashcards, spaced repetition, weak-topic detection, full question generation | planned |
| V7 | Long-term memory across sessions | planned |
| V8 | Analytics dashboard — study time, vocabulary growth, estimated band score | planned |
| V9 | Production features — auth, logging, monitoring, deployment pipeline | planned |
| V10 | AI Study Planner — proactive daily planning from weak topics & exam dates | planned |

See [`docs/roadmap.md`](docs/roadmap.md) for the complete plan.

## Development

```bash
# Backend (from backend/)
ruff check .                      # lint
pytest                            # tests (requires Python 3.13)

# Frontend (from frontend/)
npm run lint && npm run typecheck && npm run build

# Everything, isolated:
docker compose up --build -d
```

---

## Remaining Docs

- See [`docs/roadmap.md`](docs/roadmap.md) for the full version roadmap.
- The `frontend/` and `backend/` directories each contain their own developer instructions.
- See `.env.example` for environment variable reference.

---

*Built with the mandated tech stack: FastAPI, SQLAlchemy, Alembic,
PostgreSQL + pgvector, LangGraph, Next.js + TypeScript + Tailwind, Docker,
GitHub Actions.*
