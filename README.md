# LexBook AI

**LexBook AI** is an AI‑powered personal learning platform built to help you study English and prepare for IELTS/TOEFL exams. It imports your PDF study materials, extracts the text, builds embeddings, and then surfaces personalized practice questions and resources.

## Version 0 – Project Foundation

- **Backend** – FastAPI (Python 3.13+) with async SQLAlchemy, Alembic migrations, health‑check endpoint.
- **Frontend** – Next.js (React + TypeScript) with TailwindCSS, dark‑mode capable shell page that calls the backend health endpoint.
- **Database** – PostgreSQL with the `pgvector` extension (via Docker Compose).
- **Containerisation** – Docker + Docker Compose for backend, frontend, and DB.
- **CI** – GitHub Actions lint, test and build for both services.

## Quick Start (Docker)

```bash
# Clone the repo and cd into it
git clone <repo-url>
cd "LexBook AI"

# Build and start all services
docker compose up --build
```

The backend will be reachable at <http://localhost:8000> and the frontend at <http://localhost:3000>. The front page displays the backend health status.

## Project Structure

```
LexBook AI/
├─ backend/            # FastAPI service
│   ├─ app/           # Application code (API, services, core)
│   ├─ alembic/       # DB migration scripts
│   └─ Dockerfile
├─ frontend/           # Next.js UI
│   ├─ src/app/       # Pages and layout
│   └─ Dockerfile
├─ docker-compose.yml  # Orchestrates db, backend, frontend
├─ init.sql           # DB init – enable pgvector
└─ README.md
```

## Development

- **Backend** – `cd backend && pip install -e .` then `uvicorn app.main:app --reload`.
- **Frontend** – `cd frontend && npm install && npm run dev`.
- **Database migrations** – `alembic upgrade head`.

## Next Steps (Version 1 – Smart PDF Library)

- Add PDF upload endpoint.
- Extract text, store raw pages.
- Create embeddings and populate the vector store.
- Expose a search API for later RAG stages.

---

*Built with the mandated tech stack: FastAPI, SQLAlchemy, Alembic, PostgreSQL + pgvector, Next.js + TypeScript + Tailwind, Docker, GitHub Actions.*