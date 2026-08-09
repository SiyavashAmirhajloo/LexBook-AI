# Version Roadmap

Build incrementally. Each version below should be a shippable,
demoable increment — not a work-in-progress. See `CLAUDE.md` for the
overall time-budget rationale.

## Version 0 — Project Foundation

**Goal:** create a professional foundation.

Features:
- GitHub repository
- README
- Docker setup
- PostgreSQL
- pgvector
- FastAPI
- Next.js
- Initial UI
- Database connection
- Clean architecture
- CI pipeline

Resume skills demonstrated: Docker, FastAPI, PostgreSQL, clean
architecture.

## Version 1 — Smart PDF Library

**Goal:** build a local knowledge base.

Features:
- Upload PDFs
- Library view
- Delete books
- Metadata extraction
- Chunking
- Embeddings
- Vector database

Resume skills: RAG, vector search, embeddings.

## Version 2 — Semantic Chat

**Goal:** talk with your books.

Features:
- Chat interface
- Citations
- Source highlighting
- Streaming responses
- Conversation history

Resume skills: streaming, semantic search, prompt engineering.

## Version 3 — Study Sessions

**Goal:** understand what the user is learning.

Features:
- Start/finish a study session
- Chapter tracking
- Topic extraction
- Keyword extraction
- Grammar-point detection

Example: "I finished Unit 7." → system infers topics like Relative
Clauses, Passive Voice, Conditionals.

Resume skills: NLP, information extraction.

## Version 4 — Agentic Workflow

**Goal:** move beyond simple chat into agent orchestration.

Agents: `Coordinator → Study Agent → Planner → RAG Agent → Memory
Agent → Evaluation Agent`

Resume skills: LangGraph, Agentic AI.

## Version 5 — Internet Intelligence

**Goal:** find external learning resources.

Features:
- Search for IELTS questions, TOEFL questions, YouTube videos,
  articles, grammar explanations
- Present links, summaries, and recommendations (never copy
  copyrighted question text — see `docs/architecture.md`)

Resume skills: tool calling, search APIs.

## Version 6 — Personalized Learning

**Goal:** become a tutor, not just a search tool.

Features:
- Flashcards
- Vocabulary review
- Grammar review
- Practice tests
- Speaking prompts
- Writing prompts
- Reading quizzes
- Listening resources
- Weak-topic detection
- Study recommendations

Resume skills: personalization, recommendation systems.

## Version 7 — Long-Term Memory

**Goal:** remember everything relevant across sessions.

Memory scope: books, sessions, vocabulary, weaknesses, mistakes,
preferences, learning history.

Resume skills: AI memory systems, context management.

## Version 8 — Analytics Dashboard

Features:
- Charts for study time, vocabulary growth, learning curve
- Estimated IELTS band / TOEFL score
- Knowledge graph view

Resume skills: data visualization, analytics.

## Version 9 — Production Features

Features:
- Authentication
- Docker (hardened)
- Logging
- Monitoring
- Configuration management
- Deployment pipeline
- Error handling

Resume skills: production engineering.

## Version 10 — AI Study Planner

The feature expected to be most interesting to interviewers (see full
description in `docs/architecture.md`). Every day, the AI proactively
decides what to study next based on yesterday's study, weak topics,
upcoming exams, available time, vocabulary retention, and recent
mistakes — turning the project from a collection of AI features into
a genuinely intelligent assistant.

## Future Versions (post-V10, optional)

- Voice conversations
- Speaking evaluation
- Pronunciation scoring
- OCR from images
- YouTube transcript learning
- Multi-language learning (beyond Persian)
- Mobile app
- Chrome extension
- Shared workspaces
- MCP server integration
- Local LLM support via Ollama
- Broader MCP tool ecosystem
- RAG evaluation pipeline
- A/B prompt testing
- Multi-agent collaboration improvements

## Full Skill Set by Version 10

Python, FastAPI, LangGraph, Agentic AI, Retrieval-Augmented Generation
(RAG), PostgreSQL, pgvector, vector search, hybrid retrieval, embedding
models, semantic search, LLM orchestration, tool calling, prompt
engineering, memory systems, Next.js, TypeScript, Docker, CI/CD, REST
APIs, clean architecture, production AI system design, modern AI
application development.

## Presentation Advice

Treat this as a public engineering journey rather than a single
project: create a GitHub Project board, define milestones per version,
and write a short devlog after each release. The end result — a
polished app, a repo with meaningful commit history, architecture
diagrams, documentation, and a visible progression of releases — is
often as persuasive to interviewers as the finished product itself.
