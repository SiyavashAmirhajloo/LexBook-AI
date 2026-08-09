# Technology Stack

These choices are mandatory unless there is a compelling technical
reason to deviate.

## Backend

- Python 3.13+
- FastAPI
- AsyncIO
- SQLAlchemy
- Alembic
- Pydantic v2
- Uvicorn
- Background tasks
- Redis (optional, later)
- Celery (optional, later)

## AI Framework

- LangGraph (primary orchestration)
- LangChain (only where it adds clear value — don't reach for it by
  default)
- LangSmith or Langfuse for tracing (later)

## Database

- PostgreSQL
- pgvector
- Redis (later, for caching)

This PostgreSQL + pgvector combination is one of the most commonly
requested stacks in current AI engineering job postings.

## LLM Providers

Build a provider-agnostic **LLM abstraction layer** — don't lock into
one provider. Initial free/low-cost providers to support:

- Gemini (free tier)
- Groq
- OpenRouter (free models)

Later:
- Ollama (local models)
- OpenAI
- Anthropic

Order of experimentation for the abstraction layer:
`LLM Interface → Gemini → Groq → OpenRouter → Ollama → OpenAI`

## Embedding Models

Also build an abstraction layer here, supporting multiple providers:

- BAAI/bge-m3
- Jina Embeddings
- Nomic Embed
- OpenAI embeddings (optional)
- Gemini embeddings (optional)

Pick primarily for semantic search quality while staying free/efficient.

## Document Processing

- PyMuPDF
- Docling (later)
- Marker (later)
- OCR support: EasyOCR, Tesseract, Docling, Marker, PyMuPDF

## Internet Search

Build a **Search Tool interface** — don't hardcode a single provider.
Support:

- Tavily
- Brave Search API
- SerpAPI
- Google Custom Search
- DuckDuckGo

The agent should be able to choose/switch between providers.

## Frontend

- Next.js (React + TypeScript)
- TailwindCSS
- shadcn/ui
- Framer Motion
- Deployable as a PWA; consider Tauri packaging for desktop later

Recruiters respond well to seeing React, TypeScript, REST APIs,
FastAPI, authentication, and a responsive UI — a desktop-only app is
considered much less impressive for portfolio purposes.

## Authentication (later)

- JWT
- OAuth (Google)
- Guest mode (useful even for single-user/local use — demonstrates
  production readiness)

## Deployment

- Docker
- Docker Compose
- GitHub Actions
- Nginx
- Kubernetes (optional, much later)

## Testing

- Pytest
- Playwright

## Development Tooling

- VS Code
- Git / GitHub
- Postman

## Local vs. Cloud

Hybrid approach:
- Run PostgreSQL and (where possible) embeddings locally
- Use cloud only for the LLM and web search calls
- Design deployment to be configurable across three modes:
  `Local Mode → Cloud Mode → Enterprise Mode`
