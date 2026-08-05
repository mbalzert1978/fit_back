"""Create identity schema.

Revision ID: identity_001
Revises:
Create Date: 2026-08-05 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "identity_001"
down_revision = None
branch_labels = ("identity",)
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS identity")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS identity")
