"""Duenne Erfuellungen der Slice-Nahten ueber die Outbox.

Eine Klasse je Use Case, die eine Ereignis-Naht deklariert. Sie enthaelt keine
Logik - sie ist die Stelle, an der die Naht *dieses* Slice auf den gemeinsamen
Mechanismus trifft. Deshalb liegen sie hier und nicht im Slice: die Slice-Seite
soll nichts von Postgres wissen, und der Mechanismus nichts von der Naht.

Die Richtung stimmt dabei: Infrastruktur greift nach oben in die
`abstractions/` eines Context, nie umgekehrt.
"""

from src.infrastructure.outbox.publishers.identity_register_user import (
    RegisterUserOutbox,
)

__all__ = ["RegisterUserOutbox"]
