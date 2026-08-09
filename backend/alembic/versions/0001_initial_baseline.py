"""Initial baseline migration with pgvector extension."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgvector extension is available in the database
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade() -> None:
    pass