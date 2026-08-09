# AI Architecture

## Approach

Use Retrieval-Augmented Generation (RAG) as the foundation, orchestrated
through a LangGraph workflow with multiple specialized agents rather
than one monolithic chain.

## LangGraph Workflow — Core Stages

- Document ingestion
- Embedding generation
- Vector search
- Query understanding
- Topic extraction
- Web search
- Answer generation
- Citation management

## Suggested Agents

- Coordinator
- Study Agent
- RAG Agent
- Question Agent
- Internet Agent
- Planner
- Progress Tracker
- Memory Agent
- Evaluation Agent (added in later versions)
- Reflection Agent (added in later versions)

## Vector Search

- pgvector as the vector store
- Hybrid search: BM25 + vector search combined
- Reranking on top of hybrid search

Plain semantic search alone is not the target — hybrid + reranking is
noticeably more impressive and more effective.

## RAG Scope — Multimodal Ingestion

Don't stop at PDF-only RAG. Support ingesting:

- PDF
- Markdown
- Word
- PowerPoint
- HTML / web pages
- YouTube transcripts
- Audio transcripts
- Images (via OCR)

This is what qualifies the project as "multimodal RAG" rather than
basic document QA.

## Memory

Multiple memory types, not just a single conversation buffer:

- Long-term memory
- Conversation memory
- Learning memory
- Study progress memory
- Weakness memory
- Vocabulary memory

This is what differentiates an AI tutor from a stateless chatbot.

## Question Sourcing & Copyright

Do not scrape or store copyrighted question banks (e.g. Cambridge
books) directly. Preferred sources:

- Official: ETS, British Council, IDP
- Educational: Magoosh, TestGlider, BestMyTest, IELTS Liz, E2Language
- Plus: YouTube, Reddit, blogs, official documentation

**Copyright handling (important):** never persist copyrighted question
text. Instead:
- Retrieve and store links/URLs
- Summarize instead of copying
- Generate similar (original) practice questions instead of storing
  the source questions verbatim

This is both the legally safer and the more technically interesting
option (it forces you to build "generate similar question" capability
rather than a simple scraper).

## Evaluation

Most personal projects skip this — don't. Include:

- RAG evaluation
- Agent evaluation
- Prompt evaluation
- Retrieval precision metrics
- Groundedness checks
- Hallucination detection
- Citation accuracy checks

## Observability

- Langfuse
- OpenTelemetry
- MLflow
- Prompt logging
- Latency, token usage, and cost tracking

## Abstraction Layers (cross-cutting)

Build these as swappable interfaces rather than hardcoded integrations:

- LLM abstraction layer (provider-agnostic)
- Embedding abstraction layer (provider-agnostic)
- Search abstraction layer (provider-agnostic)

## Notable "Resume-Worthy" AI Capabilities to Aim For

Agentic workflow (LangGraph), hybrid retrieval, query rewriting,
metadata filtering, reranking, tool calling, structured outputs,
multi-agent collaboration, memory, reflection agent, self-evaluation,
hallucination detection, citation grounding, streaming responses,
async FastAPI, Docker, PostgreSQL + pgvector, background workers,
prompt versioning, LLM/embedding/search abstraction layers, evaluation
pipeline, observability, CI/CD, modular clean architecture.

## Standout Feature: AI Study Planner Agent

A feature most similar projects skip. Instead of only responding to
requests, it proactively plans learning:

- Analyzes what was studied today
- Identifies weak topics
- Estimates IELTS/TOEFL readiness
- Recommends the next chapter
- Schedules spaced repetition
- Chooses whether the next session should focus on reading, listening,
  vocabulary, grammar, writing, or speaking

This feature ties together RAG, agent orchestration, memory, planning,
and personalized recommendations in one place — it's both genuinely
useful for daily study and a strong interview talking point.
