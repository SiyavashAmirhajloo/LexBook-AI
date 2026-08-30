"""Add long_term_facts and vocabulary tables (V7 Long-Term Memory)."""

import sqlalchemy as sa

from alembic import op

revision = "0007_add_memory"
down_revision = "0006_add_personalization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "long_term_facts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("fact", sa.Text(), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_long_term_facts_category", "long_term_facts", ["category"])

    op.create_table(
        "vocabulary",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("word", sa.String(128), nullable=False, unique=True),
        sa.Column("translation", sa.String(256), nullable=False, server_default=""),
        sa.Column("part_of_speech", sa.String(32), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="learning"),
        sa.Column("seen_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("topic", sa.String(256), nullable=False, server_default="general"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_vocabulary_status", "vocabulary", ["status"])
    op.create_index("ix_vocabulary_topic", "vocabulary", ["topic"])


def downgrade() -> None:
    op.drop_table("vocabulary")
    op.drop_table("long_term_facts")
