# LexBook AI — Project Guide

> Working name: **LexBook AI** (replace with a final name later).

## Elevator Pitch

LexBook AI is an AI-powered personal learning platform that combines
Retrieval-Augmented Generation (RAG), Agentic AI, semantic search,
long-term memory, and web intelligence to turn static study materials
into an interactive learning experience.

Unlike a plain "chat with PDF" app, LexBook AI understands what the
learner is currently studying, tracks learning progress over time,
retrieves relevant educational resources from the web, generates
personalized practice questions, and acts as an intelligent study
companion.

The first supported domain is **English language learning and
IELTS/TOEFL preparation**, but the architecture should be designed so
any educational subject could be plugged in later. Frame this
internally as an **AI Agentic Learning Platform** whose first use case
is IELTS/TOEFL — not as "an English learning app." That framing should
drive naming, module boundaries, and extensibility decisions.

## Main Goals

- Learn English more efficiently (the owner's personal daily-use goal)
- Improve IELTS & TOEFL scores
- Build a production-grade AI application
- Demonstrate modern AI engineering skills (this project doubles as a
  portfolio / resume piece)
- Showcase Agentic AI and RAG expertise
- Serve as a flagship portfolio project

## Core Workflow

1. User imports one or more PDF books (grammar, vocabulary, IELTS/TOEFL
   prep books, etc.).
2. The system extracts text, creates embeddings, and stores everything
   in PostgreSQL + pgvector.
3. While studying, the user tells the app something like "I finished
   Chapter 3 of English Grammar in Use" or "I just studied the section
   about Relative Clauses."
4. The app identifies the document being referenced, retrieves the
   relevant content, determines the main learning topics, and extracts
   keywords/related concepts.
5. Based on those topics, the app searches the internet for
   high-quality IELTS/TOEFL learning material (practice questions,
   exercises, reading passages, listening resources, writing prompts,
   speaking questions, explanations, reputable educational sites).
6. Results are presented in a clean, organized UI.

## How to Use These Docs

This project description was split into focused files so each can be
loaded as context independently:

- `docs/tech-stack.md` — mandated technology choices, by layer
- `docs/architecture.md` — AI/RAG architecture, agent design, memory,
  abstraction layers, evaluation & observability
- `docs/requirements.md` — functional & non-functional requirements,
  learning features, UI, scale, supported languages
- `docs/roadmap.md` — the version-by-version build plan (V0–V10+),
  what "resume skill" each version demonstrates, and realistic time
  estimates

## Guiding Principle: Build in Versions

This is a large scope. Do **not** attempt to build the whole platform
at once — that consistently fails. Build it version by version (see
`docs/roadmap.md`), where each version is a shippable, demoable
increment. A finished, focused feature set beats an ambitious,
half-built system, both for daily use and for portfolio value.

Rough time expectations (working consistently, solo):
- Minimal usable app: 3–4 weeks
- Strong portfolio project: 2–3 months
- Project that could impress AI engineering interviewers: 4–6 months
- Production-quality app comparable to a startup MVP: 8–12 months

Things intentionally postponed unless truly needed: Kubernetes,
microservices, multi-user SaaS, Redis clustering, distributed workers,
a mobile app, non-English/Persian language support, enterprise
features.

Things never to cut: LangGraph, FastAPI, PostgreSQL + pgvector, hybrid
RAG, tool calling, web search, memory, streaming responses, a genuinely
good UI, Docker, an evaluation pass, clean GitHub history, and a
working demo.
