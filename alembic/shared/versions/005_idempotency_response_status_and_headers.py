"""Halte an der Reservierung fest, *wie* die erste Antwort aussah.

Gespeichert war bisher nur `response_body`. Der Replay musste sich Statuscode
und Kopfzeilen daher ausdenken - er antwortete fest mit `200` und ohne
`Location`/`Content-Language`. Eine wiederholte Registrierung bekam damit eine
*andere* Antwort als der Erstversuch, und genau das soll ein Idempotency-Key
verhindern.

Beide Spalten sind nullable: die Zeilen, die es vor dieser Migration schon gab,
kennen weder Status noch Kopfzeilen. `NULL` heisst dort "nicht aufgezeichnet",
und der Replay faellt auf sein altes Verhalten zurueck.

Revision ID: shared_005
Revises: shared_004
Create Date: 2026-08-24 18:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "shared_005"
down_revision = "shared_004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Aktualisiere Datenbankschema."""
    op.add_column(
        "idempotency_keys",
        sa.Column("response_status", sa.SmallInteger(), nullable=True),
        schema="shared_kernel",
    )
    op.add_column(
        "idempotency_keys",
        sa.Column("response_headers", sa.Text(), nullable=True),
        schema="shared_kernel",
    )


def downgrade() -> None:
    """Entferne Datenbankschema-Änderungen."""
    op.drop_column("idempotency_keys", "response_headers", schema="shared_kernel")
    op.drop_column("idempotency_keys", "response_status", schema="shared_kernel")
