"""Create recipes schema.

Revision ID: recipes_001
Revises:
Create Date: 2026-08-05 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "recipes_001"
down_revision = None
branch_labels = ("recipes",)
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS recipes")


def downgrade() -> None:
    """Downgrade database schema."""
    op.execute("DROP SCHEMA IF EXISTS recipes")
