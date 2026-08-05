"""Create shared_kernel schema.

Revision ID: shared_001
Revises:
Create Date: 2026-08-05 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "shared_001"
down_revision = None
branch_labels = ("shared",)
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS shared_kernel")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS shared_kernel")
