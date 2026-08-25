"""Create identity.refresh_tokens table.

Revision ID: identity_003
Revises: identity_002
Create Date: 2026-08-22 09:00:00.000000

Zeitpunkte als `bigint` Unix-Sekunden gemaess
docs/decisions/2026-08-06-1340-unix-epoch-statt-datetime.md - kein `timestamptz`.

Nur die Spalten, die die Ausstellung braucht. Rotation und Reuse-Detection sind
Ticket #53; ihre Spalten entstehen dort, wo sie auch gelesen werden.
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "identity_003"
down_revision = "identity_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Aktualisiere Datenbankschema."""
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        # Der Hash, nie der Token selbst: wer die Tabelle liest, koennte sich
        # sonst als jeder Nutzer ausgeben. Zum Einloesen (#52) reicht der Hash,
        # den Klartext bringt der Aufrufer mit.
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("issued_at", sa.BigInteger(), nullable=False),
        sa.Column("expires_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        # Mit dem Konto faellt auch, womit man sich fuer es ausweisen koennte.
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["identity.users.id"],
            name="fk_refresh_tokens_user_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        schema="identity",
    )
    op.create_index(
        "ix_refresh_tokens_user_id",
        "refresh_tokens",
        ["user_id"],
        schema="identity",
    )


def downgrade() -> None:
    """Entferne Datenbankschema-Änderungen."""
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens", schema="identity")
    op.drop_table("refresh_tokens", schema="identity")
