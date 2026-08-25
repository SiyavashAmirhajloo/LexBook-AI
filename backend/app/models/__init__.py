"""Models package. Exports ORM classes for Alembic autogenerate."""

from app.models.conversations import Conversation, Message
from app.models.documents import Base, Document, DocumentChunk
from app.models.personalization import (
    Flashcard,
    Prompt,
    QuizAttempt,
    QuizQuestion,
    UserProgress,
)
from app.models.study_resources import StudyResource
from app.models.study_sessions import StudySession

__all__ = [
    "Base",
    "Document",
    "DocumentChunk",
    "Conversation",
    "Message",
    "StudySession",
    "StudyResource",
    "Flashcard",
    "Prompt",
    "QuizQuestion",
    "QuizAttempt",
    "UserProgress",
]
