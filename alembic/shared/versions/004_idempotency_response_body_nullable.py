"""Make shared_kernel.idempotency_keys.response_body nullable.

NULL heisst ab jetzt "der Schluessel ist belegt, die Antwort steht noch aus".
Damit wird die Zeile zur **Reservierung**: sie entsteht, bevor die Anfrage
verarbeitet wird, nicht danach. Vorher liess sich der Vorgang nicht abbilden,
weil es die Zeile erst gab, wenn es auch schon eine Antwort gab - und genau in
dieser Luecke lief die zweite, gleichzeitige Anfrage mit demselben Schluessel
ungehindert durch.

Revision ID: shared_004
Revises: shared_003
Create Date: 2026-08-06 17:10:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "shared_004"
down_revision = "shared_003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.alter_column(
        "idempotency_keys",
        "response_body",
        existing_type=sa.Text(),
        nullable=True,
        schema="shared_kernel",
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Reservierungen ohne Antwort koennen unter der alten Regel nicht existieren.
    op.execute("DELETE FROM shared_kernel.idempotency_keys WHERE response_body IS NULL")
    op.alter_column(
        "idempotency_keys",
        "response_body",
        existing_type=sa.Text(),
        nullable=False,
        schema="shared_kernel",
    )
