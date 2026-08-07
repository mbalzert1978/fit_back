"""Create identity.users table.

Revision ID: identity_002
Revises: identity_001
Create Date: 2026-08-06 12:05:00.000000

Zeitpunkte als `bigint` Unix-Sekunden gemaess
docs/decisions/2026-08-06-1340-unix-epoch-statt-datetime.md - kein `timestamptz`.
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "identity_002"
down_revision = "identity_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Aktualisiere Datenbankschema."""
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        # Normalisiert (casefold) bereits beim Eintreffen - die Eindeutigkeit
        # gilt fuer die Adresse, nicht fuer ihre Schreibweise. Die
        # Normalisierung macht `Email.parse`, nicht die Datenbank: eine
        # Funktions-Indexdefinition muesste dieselbe Regel ein zweites Mal
        # ausdruecken und koennte von ihr abweichen.
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("locale", sa.Text(), nullable=False),
        sa.Column("time_zone_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("registered_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        # Der Unique-Constraint ist die Instanz, die ueber die Eindeutigkeit
        # entscheidet - deshalb fragt der Slice sie nicht vorab, sondern schreibt
        # und liest ihr Urteil aus dem Ergebnis
        # (.rules/python/python-feature-slices.md, "Eine Frage, die nur die
        # Gegenseite beantworten kann, wird nicht vorab gestellt").
        sa.UniqueConstraint("email", name="uq_users_email"),
        schema="identity",
    )


def downgrade() -> None:
    """Entferne Datenbankschema-Änderungen."""
    op.drop_table("users", schema="identity")
