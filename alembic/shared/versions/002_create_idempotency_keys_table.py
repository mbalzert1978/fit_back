"""Create shared_kernel.idempotency_keys table.

Revision ID: shared_002
Revises: shared_001
Create Date: 2026-08-05 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "shared_002"
down_revision = "shared_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Aktualisiere Datenbankschema."""
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("key", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("request_hash", sa.VARCHAR(64), nullable=False),
        sa.Column("response_body", sa.Text(), nullable=False),
        sa.Column(
            "created_utc", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_idempotency_keys_key"),
        schema="shared_kernel",
    )
    # Index for TTL cleanup queries
    op.create_index(
        "idx_idempotency_keys_user_created",
        "idempotency_keys",
        ["user_id", "created_utc"],
        schema="shared_kernel",
    )


def downgrade() -> None:
    """Entferne Datenbankschema-Änderungen."""
    op.drop_table("idempotency_keys", schema="shared_kernel")
