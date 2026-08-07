"""Create health_sync schema.

Revision ID: health_001
Revises:
Create Date: 2026-08-05 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "health_001"
down_revision = None
branch_labels = ("health",)
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS health_sync")


def downgrade() -> None:
    """Downgrade database schema."""
    op.execute("DROP SCHEMA IF EXISTS health_sync")
