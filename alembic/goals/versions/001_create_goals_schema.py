"""Create goals schema.

Revision ID: goals_001
Revises:
Create Date: 2026-08-05 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "goals_001"
down_revision = None
branch_labels = ("goals",)
depends_on = None


def upgrade() -> None:
    """Aktualisiere Datenbankschema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS goals")


def downgrade() -> None:
    """Entferne Datenbankschema-Änderungen."""
    op.execute("DROP SCHEMA IF EXISTS goals")
