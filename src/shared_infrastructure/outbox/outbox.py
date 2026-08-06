"""Der Schreibvorgang der Outbox - Zeile anlegen und den Zusteller wecken.

Dieses Modul ist **Mechanismus, keine Naht**. Es formuliert keine Schnittstelle,
die ein Slice zu erfuellen haette, sondern ist die Bibliothek, die eine duenne
Slice-Implementierung aufruft - dieselbe Rolle, die `idna` fuer die
E-Mail-Pruefung spielt.

Der eigentliche Trick steckt darin, was *nicht* passiert: es wird nicht
committet. Die Zeile entsteht in der Transaktion des Aufrufers, gemeinsam mit
seinem Aggregate-Write. Damit gibt es die beiden Ausgaenge "Aggregat gespeichert,
Event verloren" und "Event verschickt, Aggregat verworfen" nicht - genau dafuer
existiert eine Outbox.
"""

import json
from collections.abc import Mapping
from typing import Protocol
from uuid import UUID, uuid7

from sqlalchemy import TextClause, text

from src.shared_kernel.events import JsonValue
from src.shared_kernel.timestamp import Timestamp

__all__ = [
    "OUTBOX_CHANNEL",
    "OutboxTransaction",
    "write_event",
]

OUTBOX_CHANNEL = "outbox_events"
"""LISTEN/NOTIFY-Kanal, auf dem der Relay-Worker geweckt wird."""


class OutboxTransaction(Protocol):
    """Der Ausfuehrungskanal in der laufenden Transaktion des Aufrufers.

    Bewusst genau eine Methode - kein `commit`, kein `rollback`. Was dieses
    Modul nicht kann, kann es auch nicht versehentlich tun.

    Positional-only, damit `AsyncSession.execute` und `AsyncConnection.execute`
    beide passen; die beiden benennen ihren zweiten Parameter unterschiedlich
    (`params` bzw. `parameters`).
    """

    async def execute(
        self,
        statement: TextClause,
        parameters: Mapping[str, object] | None = None,
        /,
    ) -> object:
        """Fuehre ein Statement in der laufenden Transaktion aus."""
        ...


_INSERT_EVENT: TextClause = text("""
    INSERT INTO shared_kernel.outbox (id, event_type, payload, occurred_at, next_attempt_at)
    VALUES (:id, :event_type, CAST(:payload AS jsonb), :occurred_at, :occurred_at)
""")

# `pg_notify` statt `NOTIFY <kanal>`: NOTIFY ist reine Syntax und nimmt keine
# gebundenen Parameter, weshalb der Kanalname sonst in den SQL-String
# interpoliert werden muesste. Der Aufruf ist ebenso transaktional - Postgres
# stellt die Benachrichtigung erst beim Commit zu, also nie fuer eine Zeile, die
# es am Ende gar nicht gibt.
_NOTIFY: TextClause = text("SELECT pg_notify(:channel, '')")


async def write_event(
    transaction: OutboxTransaction,
    event_type: str,
    payload: Mapping[str, JsonValue],
    occurred_at: Timestamp,
) -> UUID:
    """Lege ein Event in die Outbox und wecke den Zusteller - in der laufenden Transaktion.

    Gibt die vergebene `event_id` zurueck. Diese ist eine UUIDv7: Postgres
    vergleicht `uuid` byteweise und UUIDv7 traegt den Zeitanteil vorne, sodass
    `ORDER BY id` bereits die Erzeugungsreihenfolge ist - eine eigene
    Sortierspalte braucht es nicht.
    """
    event_id = uuid7()
    await transaction.execute(
        _INSERT_EVENT,
        {
            "id": event_id,
            "event_type": event_type,
            "payload": json.dumps(payload),
            "occurred_at": occurred_at.unix_seconds,
        },
    )
    await transaction.execute(_NOTIFY, {"channel": OUTBOX_CHANNEL})
    return event_id
