A:

i want to bield an app for myself.
i give it (locally) my resources and books (pdf files) which i study them to learn english.
then, i can tell the app that i read a part of book A. the app must retrive the data from documents, and figure out the subject that i study. then search the internet and show me ielts and toefl questions related to that subject.
i want to use lang_graph, postgresql and pgvector, free llm api and fast api and an simple but beautfull UI. the rest can be your decision.



B:

I'd want answers to a few questions because they'll significantly affect the architecture:

1. **Platform**
   
   * Desktop (Windows)?
   
   * Web app?
   
   * Mobile?
   
   * Cross-platform (Electron/Tauri/Flutter)?

2. **Local vs Cloud**
   
   * Should **everything** run locally except the free LLM API?
   
   * Or can PostgreSQL, embeddings, etc., be hosted remotely?

3. **Internet Search**
   
   * Do you want to use:
     
     * Google Search API
     
     * Tavily
     
     * SerpAPI
     
     * Bing
     
     * Web scraping
     
     * Or let the AI decide?

4. **Question Sources**
   
   * Should it find only **official** IELTS/TOEFL practice questions?
   
   * Or also use educational websites, Reddit discussions, YouTube, blogs, Cambridge books, etc.?

5. **Copyright**
   
   * Do you want the app to retrieve links to questions, summarize them, or generate similar questions? (This affects legal and technical design.)

6. **Learning Features**  
   Besides question retrieval, should it also:
   
   * create flashcards,
   
   * explain grammar,
   
   * generate quizzes,
   
   * spaced repetition,
   
   * vocabulary lists,
   
   * pronunciation practice,
   
   * writing correction,
   
   * speaking evaluation,
   
   * progress tracking?

7. **Scale**
   
   * 20 PDFs?
   
   * 500 PDFs?
   
   * Unlimited?

8. **LLMs**  
   Do you want to stay completely free? For example:
   
   * Gemini Free
   
   * Groq
   
   * OpenRouter free models
   
   * Together AI free models
   
   * Hugging Face Inference API
   
   * or allow local models via Ollama?

* * *

If I ignore those unknowns, this is how I would write the prompt professionally.

* * *

Professional Prompt
-------------------

You are a senior AI software architect and full-stack engineer specializing in RAG systems, AI agents, LangGraph, FastAPI, PostgreSQL, and modern application architecture.

I want to build a **personal AI-powered English learning assistant** for my own use. The application should help me study for the IELTS and TOEFL exams using my own study materials while enriching them with external educational resources.

### Project Overview

The application will serve as an intelligent study companion.

I will provide my English-learning resources locally, primarily PDF books, grammar books, vocabulary books, IELTS preparation books, TOEFL preparation books, and other study materials.

The application should ingest these documents, index them, understand their contents, and use them as the primary knowledge source.

* * *

Main Workflow
-------------

1. I import one or more PDF books.

2. The system extracts text, creates embeddings, and stores everything in a PostgreSQL database using pgvector.

3. While studying, I can tell the application something like:

> "I finished Chapter 3 of English Grammar in Use."

or

> "I just studied the section about Relative Clauses."

4. The application should:
* identify which document I am referring to,

* retrieve the relevant content,

* understand the concepts I have just studied,

* determine the main learning topics,

* extract keywords and related concepts.
5. Based on those topics, the application should search the internet for high-quality IELTS and TOEFL learning materials, including:
* practice questions,

* exercises,

* grammar questions,

* vocabulary questions,

* reading passages,

* listening resources,

* writing prompts,

* speaking questions,

* explanations,

* reputable educational websites.
6. The application should present those resources in a clean and organized interface.

* * *

Technology Stack
----------------

These technologies are mandatory unless there is a compelling technical reason to replace them.

### Backend

* Python

* FastAPI

* LangGraph

* PostgreSQL

* pgvector

* SQLAlchemy

### AI

Use free or open LLM APIs whenever possible.

Examples include:

* Gemini Free

* Groq

* OpenRouter free models

* Hugging Face Inference API

Choose the most appropriate model for each task.

### Embeddings

Select an embedding model that provides excellent semantic search quality while remaining free and efficient.

### Document Processing

Use reliable libraries for:

* PDF parsing

* chunking

* metadata extraction

* OCR if necessary

### Frontend

Design a modern, clean, minimal, and visually appealing interface.

Requirements:

* responsive design

* dark mode

* intuitive navigation

* smooth animations where appropriate

* beautiful typography

* dashboard-style layout

The UI should prioritize productivity over unnecessary visual complexity.

* * *

AI Architecture
---------------

Use Retrieval-Augmented Generation (RAG).

Design a LangGraph workflow that includes:

* document ingestion

* embedding generation

* vector search

* query understanding

* topic extraction

* web search

* answer generation

* citation management

Use separate agents where appropriate.

* * *

Functional Requirements
-----------------------

The application should support:

* PDF library management

* semantic search across books

* study session tracking

* chapter completion tracking

* automatic topic extraction

* retrieval of related IELTS materials

* retrieval of related TOEFL materials

* citations to both local documents and web sources

* conversation history

* persistent memory

* * *

Non-Functional Requirements
---------------------------

The application should be:

* modular

* scalable

* maintainable

* production-quality

* well documented

* type-safe

* asynchronous where beneficial

* easy to extend

* * *

Expected Deliverables
---------------------

Please design the complete system, including:

1. Overall architecture

2. Folder structure

3. Database schema

4. LangGraph workflow

5. RAG pipeline

6. API design

7. UI architecture

8. Technology choices with justification

9. Security considerations

10. Deployment strategy

11. Future improvements

12. Recommended open-source libraries

13. Development roadmap divided into milestones

The final architecture should follow current best practices for AI applications in 2026, emphasizing clean architecture, modularity, maintainability, and extensibility.





A:

**you know, i want to use this product to study english more efficient. but also i want it to be a good resume.** 
check these job offers. based on these, tell me which option is better for Platform, Local vs Cloud, Internet Search, Question Sources, Copyright, Learning Features, Scale, LLMs, supported languages and ...

(some job offers)





B:

Because your goal is **both**:

1. Build something you'll actually use every day to get a high IELTS/TOEFL score.

2. Have a project that makes recruiters say _"This person can build production AI systems."_

I would optimize for **engineering depth**, not just features.

I couldn't reliably access the individual JobVision pages because they're behind dynamic pages, but I did compare them with current AI Engineer, LLM Engineer, and Agentic AI job requirements. They are remarkably consistent: companies repeatedly ask for Python, FastAPI, LangGraph/LangChain, RAG, vector databases (especially pgvector), PostgreSQL, Docker, cloud deployment, async APIs, evaluation, observability, and production-ready architecture. ([EPAM](https://careers.epam.com/en/vacancy/senior-ai-engineer-agentic-and-rag-systems-blty5mp8mok8tyd6a36_en?utm_source=chatgpt.com "Senior AI Engineer, Agentic and RAG Systems | Remote Work With EPAM"))

* * *

My recommendation
=================

Don't build

> "an English learning app"

Build

> **An AI Agentic Learning Platform**

English learning is simply the first application.

That single wording makes the project much stronger on a resume.

* * *

Platform
========

Recommendation
--------------

**Web Application**

Backend

* FastAPI

Frontend

* Next.js (React + TypeScript)

Deployable as a PWA.

Later you can package it with Tauri for desktop.

Why?

Recruiters love seeing

* React

* TypeScript

* REST APIs

* FastAPI

* Authentication

* Responsive UI

A desktop-only app is much less impressive.

**Resume value: 10/10**

* * *

Backend
=======

Python

FastAPI

AsyncIO

SQLAlchemy

Alembic

Pydantic v2

Background Tasks

Redis

Celery (optional)

* * *

Database
========

PostgreSQL

pgvector

Redis

This is one of the most requested combinations for AI products. ([EPAM](https://careers.epam.com/en/vacancy/senior-ai-engineer-agentic-and-rag-systems-blty5mp8mok8tyd6a36_en?utm_source=chatgpt.com "Senior AI Engineer, Agentic and RAG Systems | Remote Work With EPAM"))

* * *

Local vs Cloud
==============

Hybrid.

Store everything locally.

Run PostgreSQL locally.

Run embeddings locally if possible.

Use cloud only for

* LLM

* Web Search

Later make deployment configurable.
    Local Mode

    ↓

    Cloud Mode

    ↓

    Enterprise Mode

This demonstrates good software architecture.

* * *

Vector Search
=============

pgvector

Hybrid Search

BM25 + Vector Search

Reranking

This is much more impressive than simple semantic search.

* * *

LLMs
====

Don't lock yourself into Gemini.

Build an abstraction layer.
    LLM Interface

    ↓

    Gemini

    ↓

    Groq

    ↓

    OpenRouter

    ↓

    Ollama

    ↓

    OpenAI

Every recruiter likes seeing provider-independent architecture.

* * *

Embeddings
==========

Also abstract.

Support

* BGE

* Jina

* Nomic

* OpenAI embeddings

* Gemini embeddings

* * *

Agent Framework
===============

LangGraph

Multiple agents.

For example
    Coordinator

    ↓

    Study Agent

    ↓

    RAG Agent

    ↓

    Question Agent

    ↓

    Internet Agent

    ↓

    Planner

    ↓

    Progress Tracker

    ↓

    Memory Agent

This demonstrates Agentic AI.

* * *

Internet Search
===============

Don't hardcode Google.

Create a Search Tool interface.

Support

* Tavily

* Brave Search

* SerpAPI

* Google Custom Search

* DuckDuckGo

Then your Agent chooses.

* * *

Question Sources
================

Don't scrape Cambridge books.

Use

Official

* ETS

* British Council

* IDP

Educational

* Magoosh

* TestGlider

* BestMyTest

* IELTS Liz

* E2Language

Plus

YouTube

Reddit

Blogs

Official documentation

Store URLs instead of copyrighted content.

* * *

Copyright
=========

Very important.

Don't save copyrighted questions.

Instead

Retrieve

Summarize

Link

Generate similar questions

This is legally much safer.

* * *

RAG
===

Don't stop at PDF RAG.

Support

PDF

Markdown

Word

PowerPoint

HTML

Web pages

YouTube transcripts

Audio transcripts

Images

OCR

Now recruiters see

"Multimodal RAG"

* * *

OCR
===

Support

EasyOCR

Tesseract

Docling

Marker

PyMuPDF

* * *

Memory
======

Very important.

Use

Long-term memory

Conversation memory

Learning memory

Study progress memory

Weakness memory

Vocabulary memory

This becomes an AI tutor instead of a chatbot.

* * *

Learning Features
=================

Instead of only searching questions:

After every study session

The system should

✓ summarize

✓ extract concepts

✓ explain difficult parts

✓ generate flashcards

✓ create Anki deck

✓ build vocabulary list

✓ generate IELTS questions

✓ generate TOEFL questions

✓ generate grammar exercises

✓ speaking questions

✓ writing prompts

✓ reading quizzes

✓ listening recommendations

✓ estimate mastery

✓ schedule spaced repetition

✓ recommend next chapter

This demonstrates intelligent orchestration.

* * *

User Tracking
=============

One of the strongest resume features.

Track

Books read

Pages read

Time studied

Vocabulary learned

Grammar topics

Mistakes

Weaknesses

Predicted IELTS band

Predicted TOEFL score

Learning graph

* * *

Evaluation
==========

Most personal projects ignore this.

You shouldn't.

Include

RAG Evaluation

Agent Evaluation

Prompt Evaluation

Retrieval precision

Groundedness

Hallucination detection

Citation accuracy

* * *

Observability
=============

Another huge resume booster.

Integrate

Langfuse

OpenTelemetry

MLflow

Prompt logging

Latency

Token usage

Cost

* * *

Authentication
==============

JWT

OAuth (Google)

Guest Mode

Even for yourself.

Shows production readiness.

* * *

Deployment
==========

Docker

Docker Compose

GitHub Actions

Nginx

Optional Kubernetes later.

* * *

Languages
=========

Do **not** build only English.

Support

* English

* Persian

* Arabic

* German

* French

* Spanish

Keep every prompt multilingual.

This only requires good architecture.

* * *

UI
==

Next.js

TypeScript

TailwindCSS

shadcn/ui

Framer Motion

Charts

Dark mode

Chat interface

Knowledge graph

Study dashboard

Timeline

Flashcards

Progress analytics

* * *

Scale
=====

Design for
    1 user today

    ↓

    100 users

    ↓

    1000 users

    ↓

    Multi-tenant SaaS

Even if you never deploy publicly.

* * *

Resume-worthy AI Features
=========================

These are the things interviewers will ask about:

* Agentic workflow (LangGraph)

* Hybrid retrieval

* Query rewriting

* Metadata filtering

* Reranking

* Tool calling

* Structured outputs

* Multi-agent collaboration

* Memory

* Reflection agent

* Self-evaluation

* Hallucination detection

* Citation grounding

* Streaming responses

* Async FastAPI

* Docker

* PostgreSQL + pgvector

* Background workers

* Prompt versioning

* LLM abstraction layer

* Embedding abstraction layer

* Search abstraction layer

* Evaluation pipeline

* Observability

* CI/CD

* Modular Clean Architecture

* * *

The one feature I'd add that almost no one includes
---------------------------------------------------

An **AI Study Planner Agent**.

Instead of waiting for you to ask for questions, it proactively plans your learning:

* analyzes what you studied today,

* identifies weak topics,

* estimates your IELTS/TOEFL readiness,

* recommends the next chapter,

* schedules spaced repetition,

* chooses whether your next session should focus on reading, listening, vocabulary, grammar, writing, or speaking.

This ties together RAG, agent orchestration, memory, planning, and personalized recommendations in a single feature. It is genuinely useful for your own learning and showcases many of the production AI engineering skills that current AI/LLM engineering roles are seeking. ([EPAM](https://careers.epam.com/en/vacancy/senior-ai-engineer-agentic-and-rag-systems-blty5mp8mok8tyd6a36_en?utm_source=chatgpt.com "Senior AI Engineer, Agentic and RAG Systems | Remote Work With EPAM"))



A:

wow. this is huge. do you think that i can handle it alone? answer honestly.



B:

Yes, but **not if you try to build all of it at once.**

Since we've talked before about your background, I know you have experience with Python, PyTorch, FastAPI (at a beginner level), LangGraph, RAG concepts, and you've completed several AI projects. You're not starting from zero. At the same time, you've also mentioned that you're still building confidence with production engineering topics like Docker, deployment, and some AI infrastructure.

So my honest assessment is:

### Could you build the final vision alone?

**Yes.**

### Could you build it in 2-3 months?

**No.**

### Could you build a resume-worthy version in 2-3 months?

**Absolutely.**

* * *

Here's what usually happens
---------------------------

Many people think:

> "I'll build ChatGPT for learning English."

Then they start implementing:

* RAG

* Multi-agent system

* Memory

* Flashcards

* Web search

* UI

* Docker

* Authentication

* Evaluation

* Analytics

Three months later...

Nothing is finished.

Recruiters can't evaluate unfinished architecture diagrams.

They evaluate **working software**.

* * *

What I would do if I were optimizing for your resume
----------------------------------------------------

Instead of building **one giant project**, build it in **versions**.

### Version 1 (2-3 weeks)

* PDF upload

* PostgreSQL

* pgvector

* FastAPI

* Basic RAG

* Chat with your books

Already enough for a portfolio demo.

* * *

### Version 2 (2 weeks)

Now add

* LangGraph

* Conversation memory

* Study sessions

* Topic extraction

Now it's no longer "Chat with PDF."

It's an AI study assistant.

* * *

### Version 3 (2 weeks)

Now add

* Internet search

* Retrieve IELTS resources

* Generate quizzes

* Save progress

Now recruiters see tool use.

* * *

### Version 4 (3 weeks)

Add

* Multiple agents

* Planner

* Reflection

* Citation checking

Now it becomes an Agentic AI project.

* * *

### Version 5

Then

* Docker

* CI/CD

* Authentication

* Deployment

* Observability

Now it looks like a production system.

* * *

Here's why I actually think you can do this
-------------------------------------------

I've seen the kinds of questions you've asked over the past months.

You've worked with:

* CNNs

* Transformers

* OCR

* Jetson Nano

* Kaggle

* Fine-tuning

* LoRA

* RAG

* LangGraph

* FastAPI

* PostgreSQL

* pgvector

* Prompt engineering

The difficulty isn't understanding AI concepts.

The challenge is **software engineering discipline**.

Projects like this succeed because someone keeps saying:

> "Today's goal is one endpoint."

instead of

> "Today I'll build the whole AI tutor."

* * *

What I would remove
-------------------

If your goal is getting hired within the next year, I would postpone:

* Kubernetes

* Microservices

* Multi-user SaaS

* Redis cluster

* Distributed workers

* Mobile app

* Multi-language support beyond English (unless you need Persian for your own use)

* Enterprise features

Those are nice to have.

* * *

What I would never remove
-------------------------

These are the features that make recruiters pause and look more closely:

* LangGraph

* FastAPI

* PostgreSQL + pgvector

* Hybrid RAG

* Tool calling

* Web search

* Memory

* Streaming responses

* Beautiful UI

* Docker

* Evaluation

* GitHub with clean commits

* A live demo (or a polished local demo video)

* * *

My estimate for you
-------------------

If you work consistently, here's my estimate:

* **Minimal usable app:** 3 to 4 weeks

* **Strong portfolio project:** 2 to 3 months

* **Project that could genuinely impress AI engineering interviewers:** 4 to 6 months

* **Production-quality application comparable to a startup MVP:** 8 to 12 months

The encouraging part is that you don't need the last stage to benefit from it. A polished, well-architected project with a focused feature set is often much more persuasive than an overambitious project that's only half finished.





A:

good. 

- write me a plan for versions.
- a description for project.
- tools that i will use.



B:

I actually think this project can become the **centerpiece of your portfolio** if you treat it like a real software product rather than "just another AI demo."

One thing I would change from your original idea is the scope. Don't think of it as _an English learning app_. Think of it as an **AI-powered Agentic Learning Platform** whose **first use case** is IELTS/TOEFL preparation. That small change makes your architecture much more extensible and much more attractive to recruiters.

* * *

Project Description
===================

Project Name (Temporary)
------------------------

**LexBook AI** _(replace with your final name later)_
Elevator Pitch
--------------

LexBook AI is an AI-powered personal learning platform that combines Retrieval-Augmented Generation (RAG), Agentic AI, semantic search, long-term memory, and web intelligence to transform static study materials into an interactive learning experience.

Unlike traditional PDF chat applications, LexBook AI understands what the learner is studying, tracks learning progress over time, retrieves relevant educational resources from the web, generates personalized practice questions, and acts as an intelligent study companion.

The first supported domain is English language learning and IELTS/TOEFL preparation, but the architecture is designed to support any educational subject.

* * *

Main Goals
----------

* Learn English more efficiently

* Improve IELTS & TOEFL scores

* Build a production-grade AI application

* Demonstrate modern AI engineering skills

* Showcase Agentic AI and RAG expertise

* Serve as a flagship portfolio project

* * *

Technology Stack
================

Backend
-------

* Python 3.13+

* FastAPI

* SQLAlchemy

* Alembic

* Pydantic v2

* Uvicorn

* * *

AI Framework
------------

* LangGraph

* LangChain (only where it adds value)

* LangSmith or Langfuse (later)

* * *

Database
--------

* PostgreSQL

* pgvector

* * *

Cache
-----

Later

* Redis

* * *

LLM Providers
-------------

Use an abstraction layer.

Initially support:

* Gemini

* Groq

* OpenRouter

Later

* Ollama

* OpenAI

* Anthropic

* * *

Embedding Models
----------------

Support multiple providers.

Initially

* BAAI/bge-m3

* Jina Embeddings

* Nomic Embed

* * *

Document Processing
-------------------

* PyMuPDF

* Docling (later)

* Marker (later)

* OCR support

* * *

Search
------

* Tavily

* Brave Search API

* DuckDuckGo

* * *

Frontend
--------

* Next.js

* React

* TypeScript

* TailwindCSS

* shadcn/ui

* Framer Motion

* * *

Authentication
--------------

Later

* JWT

* OAuth

* * *

Deployment
----------

* Docker

* Docker Compose

* GitHub Actions

* * *

Testing
-------

* Pytest

* Playwright

* * *

Development
-----------

* VS Code

* Git

* GitHub

* Postman

* * *

Folder Structure (High Level)
=============================

    frontend/
    
    backend/
    
    database/
    
    docker/
    
    docs/
    
    tests/
    
    scripts/
    
    .github/



* * *

Version Roadmap
===============

* * *

Version 0
=========

Project Foundation
------------------

Goal

Create a professional foundation.

### Features

* GitHub repository

* README

* Docker setup

* PostgreSQL

* pgvector

* FastAPI

* Next.js

* Initial UI

* Database connection

* Clean Architecture

* CI pipeline

Resume Skills

* Docker

* FastAPI

* PostgreSQL

* Clean Architecture

* * *

Version 1
=========

Smart PDF Library
-----------------

Goal

Build a local knowledge base.

### Features

* Upload PDFs

* Library

* Delete books

* Metadata extraction

* Chunking

* Embeddings

* Vector database

Resume Skills

* RAG

* Vector Search

* Embeddings

* * *

Version 2
=========

Semantic Chat
-------------

Goal

Talk with books.

### Features

* Chat

* Citation

* Source highlighting

* Streaming response

* Conversation history

Resume Skills

* Streaming

* Semantic Search

* Prompt Engineering

* * *

Version 3
=========

Study Sessions
--------------

Goal

Understand learning.

### Features

* Start study session

* Finish session

* Chapter tracking

* Topic extraction

* Keywords

* Grammar detection

Example

"I finished Unit 7."

↓

System understands

Relative Clauses

Passive Voice

Conditionals

Resume Skills

* NLP

* Information Extraction

* * *

Version 4
=========

Agentic Workflow
----------------

Goal

Move beyond chat.

### Agents

Coordinator

↓

Study Agent

↓

Planner

↓

RAG Agent

↓

Memory Agent

↓

Evaluation Agent

Resume Skills

* LangGraph

* Agentic AI

* * *

Version 5
=========

Internet Intelligence
---------------------

Goal

Find learning resources.

### Features

Search

* IELTS questions

* TOEFL questions

* YouTube

* Articles

* Grammar explanations

Show

* Links

* Summaries

* Recommendations

Resume Skills

* Tool Calling

* Search APIs

* * *

Version 6
=========

Personalized Learning
---------------------

Goal

Become a tutor.

### Features

Flashcards

Vocabulary

Grammar review

Practice tests

Speaking prompts

Writing prompts

Reading quizzes

Listening resources

Weak topic detection

Study recommendations

Resume Skills

* Personalization

* Recommendation Systems

* * *

Version 7
=========

Long-Term Memory
----------------

Remember everything.

### Memory

Books

Sessions

Vocabulary

Weaknesses

Mistakes

Preferences

Learning history

Resume Skills

* AI Memory

* Context Management

* * *

Version 8
=========

Analytics Dashboard
-------------------

Charts

Study time

Vocabulary growth

Learning curve

Estimated IELTS band

Estimated TOEFL score

Knowledge graph

Resume Skills

* Data Visualization

* Analytics

* * *

Version 9
=========

Production Features
-------------------

Authentication

Docker

Logging

Monitoring

Configuration

Deployment

Error handling

Resume Skills

Production Engineering

* * *

Version 10
==========

AI Study Planner
----------------

This is the feature I think will impress interviewers the most.

Every day the AI decides

"What should you study today?"

It considers

* what you studied yesterday,

* your weak topics,

* upcoming exams,

* your available time,

* your vocabulary retention,

* your recent mistakes,

then generates a personalized study plan.

This is where your project evolves from a collection of AI features into an intelligent assistant.

* * *

Future Versions
===============

* Voice conversations

* Speaking evaluation

* Pronunciation scoring

* OCR from images

* YouTube transcript learning

* Multi-language learning

* Mobile app

* Chrome extension

* Shared workspaces

* MCP server integration

* Local LLM support with Ollama

* Model Context Protocol (MCP) tool ecosystem

* RAG evaluation pipeline

* A/B prompt testing

* Multi-agent collaboration improvements

* * *

Skills Demonstrated on Your Resume
==================================

By the time you reach Version 10, you'll be able to honestly list experience with:

* Python

* FastAPI

* LangGraph

* Agentic AI

* Retrieval-Augmented Generation (RAG)

* PostgreSQL

* pgvector

* Vector Search

* Hybrid Retrieval

* Embedding Models

* Semantic Search

* LLM Orchestration

* Tool Calling

* Prompt Engineering

* Memory Systems

* Next.js

* TypeScript

* Docker

* CI/CD

* REST APIs

* Clean Architecture

* Production AI System Design

* Modern AI Application Development

* * *

One final recommendation
------------------------

Don't think of this as **one project**. Think of it as a **public engineering journey**.

Create a GitHub Project board, define milestones for each version, and write a short devlog after every major release. By the end, you'll have:

* A polished portfolio application

* A GitHub repository with meaningful commit history

* Architecture diagrams

* Documentation

* A sequence of incremental releases that demonstrates how you approach software engineering over time

For many interviewers, that progression is just as compelling as the finished application itself.
