"""Create shared_kernel.outbox table.

Revision ID: shared_003
Revises: shared_002
Create Date: 2026-08-06 15:10:00.000000

Transaktionale Outbox fuer Integration Events zwischen Bounded Contexts
(siehe CLAUDE.md, "Cross-Context-Kommunikation"). Zeitpunkte sind durchgaengig
`bigint` Unix-Sekunden gemaess docs/decisions/2026-08-06-1340-unix-epoch-statt-
datetime.md - kein `timestamptz`.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "shared_003"
down_revision = "shared_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Aktualisiere Datenbankschema."""
    op.create_table(
        "outbox",
        # UUIDv7: Identitaet und Reihenfolge in einer Spalte. Postgres vergleicht
        # `uuid` byteweise, und UUIDv7 traegt den Zeitanteil vorne - `ORDER BY id`
        # ist damit Erzeugungsreihenfolge, ohne zweite Sortierspalte.
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("occurred_at", sa.BigInteger(), nullable=False),
        # Faelligkeit des naechsten Zustellversuchs. Traegt den Backoff als
        # Zustand, damit kein Worker unter gehaltenen Row-Locks schlafen muss.
        # `0` beim Schreiben = sofort faellig; bewusst unabhaengig von
        # `occurred_at`, das ein fachlicher Zeitpunkt ist und kein Termin.
        sa.Column("next_attempt_at", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        # Zugestellt. Bewusst getrennt von `failed_at`: ein aufgegebenes Event
        # ist nicht verarbeitet, es ist liegengeblieben.
        sa.Column("processed_at", sa.BigInteger(), nullable=True),
        sa.Column("failed_at", sa.BigInteger(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("attempts >= 0", name="ck_outbox_attempts_non_negative"),
        schema="shared_kernel",
    )
    # Partieller Index exakt auf die Claim-Query des Relays: er waechst nur mit
    # der Zahl offener Events, nicht mit der Historie.
    op.create_index(
        "idx_outbox_claimable",
        "outbox",
        ["next_attempt_at", "id"],
        schema="shared_kernel",
        postgresql_where=sa.text("processed_at IS NULL AND failed_at IS NULL"),
    )


def downgrade() -> None:
    """Entferne Datenbankschema-Änderungen."""
    op.drop_index("idx_outbox_claimable", table_name="outbox", schema="shared_kernel")
    op.drop_table("outbox", schema="shared_kernel")
