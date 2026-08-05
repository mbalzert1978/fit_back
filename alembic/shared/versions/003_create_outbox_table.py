"""Create shared.outbox table for transactional event publishing.

Revision ID: shared_003
Revises: shared_002
Create Date: 2026-08-05 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "shared_003"
down_revision: str | Sequence[str] | None = "shared_002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create shared.outbox table with indices for SELECT...FOR UPDATE SKIP LOCKED."""
    # Ensure shared schema exists
    op.execute("CREATE SCHEMA IF NOT EXISTS shared")

    # Create outbox table
    op.create_table(
        "outbox",
        sa.Column("id", sa.UUID, nullable=False, primary_key=True),
        sa.Column("event_type", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("aggregate_id", sa.UUID, nullable=False),
        sa.Column("aggregate_type", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_by", sa.UUID, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text, nullable=True),
        schema="shared",
    )

    # Partial index for SELECT ... FOR UPDATE SKIP LOCKED queries (unprocessed events ordered by creation)
    op.create_index(
        "idx_outbox_unprocessed_by_created",
        "outbox",
        ["created_at"],
        schema="shared",
        postgresql_where=sa.text("processed_at IS NULL"),
    )

    # Index for processed_by to verify idempotency
    op.create_index(
        "idx_outbox_processed_by",
        "outbox",
        ["processed_by"],
        schema="shared",
    )


def downgrade() -> None:
    """Drop shared.outbox table."""
    op.drop_table("outbox", schema="shared")
