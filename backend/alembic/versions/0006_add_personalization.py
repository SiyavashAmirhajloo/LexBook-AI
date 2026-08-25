"""Add personalization tables (V6)."""

import sqlalchemy as sa

from alembic import op

revision = "0006_add_personalization"
down_revision = "0005_add_study_resources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "flashcards",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "study_session_id",
            sa.Uuid(),
            sa.ForeignKey("study_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("front", sa.Text(), nullable=False),
        sa.Column("back", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False, server_default="term"),
        sa.Column("source_topic", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_flashcards_study_session_id", "flashcards", ["study_session_id"])

    op.create_table(
        "prompts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "study_session_id",
            sa.Uuid(),
            sa.ForeignKey("study_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("source_topic", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prompts_study_session_id", "prompts", ["study_session_id"])

    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "study_session_id",
            sa.Uuid(),
            sa.ForeignKey("study_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("choices", sa.Text(), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("source_topic", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_quiz_questions_study_session_id", "quiz_questions", ["study_session_id"])

    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "question_id",
            sa.Uuid(),
            sa.ForeignKey("quiz_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chosen_index", sa.Integer(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_quiz_attempts_question_id", "quiz_attempts", ["question_id"])

    op.create_table(
        "user_progress",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("topic", sa.String(256), nullable=False, unique=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mastery", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_progress")
    op.drop_table("quiz_attempts")
    op.drop_table("quiz_questions")
    op.drop_table("prompts")
    op.drop_table("flashcards")
