"""Create study_resources table (V5 Internet Intelligence)."""

import sqlalchemy as sa

from alembic import op

revision = "0005_add_study_resources"
down_revision = "0004_add_study_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "study_resources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "study_session_id",
            sa.Uuid(),
            sa.ForeignKey("study_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("topic", sa.String(256), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("source_domain", sa.String(256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("resource_type", sa.String(32), nullable=False, server_default="general"),
        sa.Column("is_reputable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("practice_questions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_study_resources_study_session_id", "study_resources", ["study_session_id"]
    )


def downgrade() -> None:
    op.drop_table("study_resources")
