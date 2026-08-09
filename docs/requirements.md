# Requirements

## Functional Requirements

The application should support:

- PDF library management
- Semantic search across books
- Study session tracking
- Chapter completion tracking
- Automatic topic extraction
- Retrieval of related IELTS materials
- Retrieval of related TOEFL materials
- Citations to both local documents and web sources
- Conversation history
- Persistent memory

## Learning Features

After every study session, the system should be able to:

- Summarize what was studied
- Extract key concepts
- Explain difficult parts
- Generate flashcards
- Create an Anki-compatible deck
- Build a vocabulary list
- Generate IELTS questions
- Generate TOEFL questions
- Generate grammar exercises
- Generate speaking questions
- Generate writing prompts
- Generate reading quizzes
- Recommend listening resources
- Estimate topic mastery
- Schedule spaced repetition
- Recommend the next chapter to study

## User / Progress Tracking

- Books read
- Pages read
- Time studied
- Vocabulary learned
- Grammar topics covered
- Mistakes made
- Weak areas
- Predicted IELTS band
- Predicted TOEFL score
- Learning graph over time

## Supported Languages

Don't build English-only. Target multilingual support for:

- English
- Persian
- Arabic
- German
- French
- Spanish

Keep prompts multilingual-ready from the start — this is mostly an
architecture concern (don't hardcode English strings into prompts/UI
logic), not a huge amount of extra work if planned early. Note: per
the project roadmap, full non-English support is a "nice to have" that
can be postponed except for Persian, which may be needed for personal
use.

## UI Requirements

Design a modern, clean, minimal, visually appealing interface:

- Responsive design
- Dark mode
- Intuitive navigation
- Smooth animations where appropriate
- Beautiful typography
- Dashboard-style layout
- Chat interface
- Knowledge graph view
- Study dashboard
- Timeline view
- Flashcards UI
- Progress analytics / charts

The UI should prioritize productivity over unnecessary visual
complexity.

## Scale

Design with a growth path in mind, even if it's never deployed
publicly:

`1 user today → 100 users → 1,000 users → multi-tenant SaaS`

## Non-Functional Requirements

The application should be:

- Modular
- Scalable
- Maintainable
- Production-quality
- Well documented
- Type-safe
- Asynchronous where beneficial
- Easy to extend

## Deliverables (for the initial design phase)

When designing the system, produce:

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

## Suggested Folder Structure (high level)

```
frontend/
backend/
database/
docker/
docs/
tests/
scripts/
.github/
```
