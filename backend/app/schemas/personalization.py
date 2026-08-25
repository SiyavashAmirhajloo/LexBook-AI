"""Pydantic schemas for V6 personalization endpoints."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FlashcardResponse(BaseModel):
    id: UUID
    front: str
    back: str
    kind: str
    source_topic: str


class FlashcardsResponse(BaseModel):
    study_session_id: UUID
    cards: list[FlashcardResponse]


class PromptResponse(BaseModel):
    id: UUID
    kind: str
    prompt_text: str
    source_topic: str


class PromptsResponse(BaseModel):
    study_session_id: UUID
    prompts: list[PromptResponse]


class QuizQuestionResponse(BaseModel):
    id: UUID
    question: str
    choices: list[str]
    source_topic: str
    # correct_index/explanation are NOT exposed pre-answer; they come back
    # in the attempt response after the learner commits to a choice.


class QuizResponse(BaseModel):
    study_session_id: UUID
    questions: list[QuizQuestionResponse]


class QuizAttemptRequest(BaseModel):
    question_id: UUID
    chosen_index: int


class QuizAttemptResponse(BaseModel):
    attempt_id: UUID
    is_correct: bool
    correct_index: int
    explanation: str
    topic_mastery: float
    topic_attempts: int


class WeakTopicResponse(BaseModel):
    topic: str
    attempts: int
    correct: int
    mastery: float
    last_seen_at: datetime


class RecommendationResponse(BaseModel):
    recommendation: str
