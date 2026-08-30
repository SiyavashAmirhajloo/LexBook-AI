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
        ├──► Flashcards / Quizzes / Prompts ◄─── LangGraph Agent Workflow
        │    (mastery tracking, weak topics)   coordinator → planner →
        └──────────► Internet Intelligence      {rag | study | internet |
                 (curated web resources,         personalize} → memory →
                  original AI summaries +        evaluation
                  generated questions)                ▲
                                          ┌───────────┘
                                          │ all 6 memory types
                                          │ (facts, vocab, sessions,
                                          │  progress, weakness,
                                          │  conversations)
```

**Stack:** FastAPI (async) · PostgreSQL + pgvector · LangGraph · Gemini ·
fastembed · Next.js 15 + TypeScript + TailwindCSS · Docker Compose · GitHub Actions

## Quick Start

```bash
git clone https://github.com/SiyavashAmirhajloo/LexBook-AI.git
cd LexBook-AI

cp .env.example .env          # add your GEMINI_API_KEY (see file for all options)
docker compose up --build -d
```

- **Frontend UI**: <http://localhost:3000> (login / register / guest on first visit)
- **Backend API**: <http://localhost:8000/api/v1/health>
- **Interactive API docs**: <http://localhost:8000/docs>

Auth quick-start: create an account on the login page, or click **Continue as
Guest** to explore immediately. All feature routes require a session.

Migrations run automatically on container start. See `.env.example` for all
supported configuration (`EMBEDDING_PROVIDER`, `SEARCH_PROVIDER`,
`LLM_PROVIDER`, …).

## Feature Walkthrough

1. **Upload books** in `/library` — text is extracted, chunked, embedded into pgvector.
2. **Chat with your books** in `/chat` — streaming answers with clickable page-level citations; the LLM also sees what you studied and struggled with previously.
3. **Log a study session** in `/study-sessions` — say *"I finished Unit 7"*; the system resolves the book section and extracts topics/keywords.
4. **Find web resources** on any session card — curated IELTS/TOEFL links ranked by source reputation, each with an original AI-written summary and generated practice questions.
5. **Practice** via *Practice This Session* → flashcards, quizzes (with mastery tracking), and speaking/writing prompts. Then check `/review` for your weakest topics and what to study next.
6. **Long-term memory** in `/memory` — facts the app remembers, vocabulary tracked, weak topics inherited across sessions.
7. **Dashboard** in `/dashboard` — transparent estimated scores, study-time + vocab-growth curves, knowledge graph, mistake bars, session timeline.

---

## Version History

### V9 — Production Features *(current)*

Hardens the app from "working personal project" to production-shaped software.

- **Authentication** — JWT access + refresh tokens (refresh rotation with server-side revocation), bcrypt password hashing, Google OAuth (code flow + `id_token` verification against Google's JWKS), and guest mode. All `/api/v1` business routes require a bearer token; `/health/*`, `/auth/*`, and docs stay public.
- **Hardened containers** — multi-stage builds, non-root `app` user (uid 1001), `tini` for proper signal handling, `python -m` entrypoints, `--proxy-headers` behind reverse proxies.
- **Centralized configuration** — one validated `Settings` class; JWT secret auto-generates in dev but must be explicit in staging/prod; CORS allowlist is env-driven.
- **Structured logging** — JSON logs in prod (`{ts, level, logger, msg, trace_id, …}`), human-readable in dev; every error carries a `trace_id` you can grep.
- **Monitoring** — `/health/live` (liveness), `/health/ready` (DB + config checks), legacy `/health` kept.
- **Centralized errors** — every failure returns `{detail, code, trace_id, status}`; stack traces stay in the server log, never the response.
- **Deploy pipeline** — `.github/workflows/deploy.yml` builds and pushes backend/frontend images to GHCR on `main`; `v*` tags trigger a smoke test (boot stack → liveness → auth-required check → guest login) and a staging deploy hook.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/register` | Email + password signup → token pair |
| `POST` | `/api/v1/auth/login` | Email + password login → token pair |
| `POST` | `/api/v1/auth/refresh` | Rotate refresh token → new pair (old one revoked) |
| `POST` | `/api/v1/auth/logout` | Revoke the refresh token |
| `POST` | `/api/v1/auth/guest` | Anonymous session (8h) |
| `GET` | `/api/v1/auth/google/url` | Google consent URL |
| `POST` | `/api/v1/auth/google/callback` | Exchange code → user + tokens |
| `GET` | `/api/v1/auth/me` | Current user (bearer required) |
| `GET` | `/api/v1/health/live` · `/health/ready` | Liveness / readiness probes |

The frontend gained a `/login` page (sign in / register / guest), a `RequireAuth` route guard, an auth context with automatic token refresh on 401, and a logout control.

### V8 — Analytics Dashboard

Read-only dashboard that visualizes every metric the app already tracks (V2–V7). No parallel tracking system.

- **KPI tiles** — books, pages, sessions, vocab, facts, with sparkline on the vocabulary growth.
- **Estimated IELTS band + TOEFL score** — the formula and the exact inputs are returned alongside each estimate, so the prediction is auditable not black-box.
  - `weighted_mastery = 0.5*quiz_mastery + 0.3*coverage + 0.2*completion`
  - `ielts_band = 4.5 + 4.0*weighted_mastery`, rounded to nearest 0.5
  - `toefl_score = 30 + 90*weighted_mastery`
- **Charts (inline SVG, zero new dependencies)** — study time over time, vocabulary growth (running total), learning curve (daily quiz accuracy), grammar-topics mastery bar, mistakes bar.
- **Knowledge graph** — topics as nodes sized by study frequency, edges weighted by co-occurrence within sessions. Circular deterministic layout.
- **Timeline** — recent study sessions, newest first.
- **Scoring-method panel** — the exact formula printed in the dashboard, no hidden knobs.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/analytics` | One snapshot with everything: totals, all chart series, the knowledge graph, the timeline, and the transparent estimates |

The **`/dashboard`** page renders it all.

### V7 — Long-Term Memory

The app stops forgetting between sessions. Six memory types per `docs/architecture.md`, all stored in PostgreSQL — structured tables where lookup matters, no pgvector overhead for list-style data.

- **Long-term memory** — `long_term_facts` (preference / goal / fact) — durable user statements, auto-extracted from chat via the LLM, plus manual entry.
- **Conversation memory** — V2 `conversations` + `messages` (read-only here).
- **Learning memory** — V3 `study_sessions` (topics, keywords, summary, raw_input).
- **Study progress** — V6 `user_progress` (per-topic mastery, attempts, correct).
- **Weakness memory** — derived view of `user_progress` (mastery ≤ 50% with ≥ 1 attempt). Feeds the recommendation endpoint cross-session.
- **Vocabulary memory** — `vocabulary` table (word, topic, status, seen_count).

**Memory Agent** is no longer a stub — it reads a snapshot from the DB, runs LLM extraction on the user's current text, writes new facts + vocabulary, and pushes a fresh snapshot into graph state. RAG prompts now include a `What the learner already knows` block so answers draw on prior sessions, not just the current one.

**Cross-session example (real, end-to-end):**
1. Session A: quiz wrong on "Sentence Connectors" → `user_progress` updated, 0% mastery.
2. Session B: hit `/recommendation` → *"Focus on 'Sentence Connectors' next — current mastery 0% (0/1 correct)"* — driven by the prior session's data.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/memory/snapshot` | Full memory snapshot (facts, vocab, weak topics, recent sessions) |
| `GET` | `/api/v1/memory/summary` | Compact form for prompt injection |
| `GET/POST` | `/api/v1/memory/facts` | List or add a long-term fact |
| `GET/POST` | `/api/v1/memory/vocabulary` | List or add a tracked word |

The **`/memory`** page in the UI shows everything the app remembers about you.

### V6 — Personalized Learning

The app stops just retrieving and starts teaching.

- **Flashcards** — original AI-generated term/grammar/vocab cards per study session, click-to-reveal UI.
- **Quizzes** — 4-choice multiple choice generated from session topics; correct answers stay server-side until you commit, then every attempt updates a live mastery estimate.
- **Prompts** — original IELTS-style speaking questions, writing tasks, and reading exercises.
- **Weak-topic detection** — `quiz_attempts` roll up into per-topic `user_progress` (mastery = correct/attempts); `/review` ranks your weakest topics and tells you what to study next.
- **Personalization Agent** — new route in the LangGraph graph keeps tracing parity across all features.
- All generated content is ORIGINAL (copyright rule); heuristic fallbacks keep generation alive without an LLM.

| Method | Path | Description |
|--------|------|-------------|
| `POST/GET` | `/api/v1/study-sessions/{id}/flashcards` | Generate / list flashcards for a session |
| `POST/GET` | `/api/v1/study-sessions/{id}/prompts` | Generate / list speaking+writing+reading prompts |
| `POST` | `/api/v1/study-sessions/{id}/quiz` | Generate a quiz (answers hidden) |
| `POST` | `/api/v1/quiz/attempt` | Submit an answer; returns correctness + explanation + updated topic mastery |
| `GET` | `/api/v1/weak-topics?limit=8` | Lowest-mastery topics |
| `GET` | `/api/v1/recommendation` | One-line "study this next" |

### V5 — Internet Intelligence

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
