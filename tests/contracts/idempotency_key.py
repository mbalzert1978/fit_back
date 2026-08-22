"""The reserved idempotency key the register pact's third state describes.

Seeded straight against `shared_kernel.idempotency_keys` via the existing
`postgres_engine` fixture - **not** through the endpoint under verification: a
state that leans on its own subject under test proves nothing (same reasoning as
`account.py`).
"""

from typing import final

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.middleware.idempotency import ANONYMOUS_USER_ID

__all__ = ["IdempotencyKey"]

_INSERT = text(
    "INSERT INTO shared_kernel.idempotency_keys"
    " (key, user_id, request_hash, response_body, created_utc)"
    " VALUES (:key, :user_id, :request_hash, :response_body, now())"
)
_DELETE_ALL = text("DELETE FROM shared_kernel.idempotency_keys")

_FOREIGN_HASH = "0" * 64
"""Ein Hash, der zu keinem Rumpf passt, den der Vertrag schickt.

Der echte Wert entstuende aus `sha256("POST:<pfad>:<rumpf>")`; welcher Rumpf das
waere, muesste dieser Aufbau raten. Er braucht ihn nicht: der Fall lautet
"anderer Rumpf", und dafuer genuegt jeder Wert, der nicht der richtige ist.
"""

_ANSWERED = '{"data": {}}'
"""Die Antwort des ersten Versuchs, damit die Zeile keine offene Reservierung
ist: bei `response_body IS NULL` antwortete die Middleware mit
`request-in-progress` statt mit dem Wiederverwendungs-Fall.
"""


@final
class IdempotencyKey:
    """Belegt genau einen Schluessel und raeumt die Tabelle wieder leer."""

    def __init__(self, engine: AsyncEngine, *, key: str) -> None:
        self._engine = engine
        self._key = key

    async def claim_for_another_body(self) -> None:
        """Lege den Schluessel als schon beantworteten Versuch mit fremdem Rumpf ab."""
        await self.clear()
        async with self._engine.begin() as connection:
            await connection.execute(
                _INSERT,
                {
                    "key": self._key,
                    "user_id": ANONYMOUS_USER_ID,
                    "request_hash": _FOREIGN_HASH,
                    "response_body": _ANSWERED,
                },
            )

    async def clear(self) -> None:
        """Raeume alle Schluessel weg - auch die, die eine Interaktion selbst anlegt.

        Der Vertrag schickt fuer mehrere Interaktionen denselben
        `Idempotency-Key`: jede ist eine eigene Welt, in der er noch frei ist.
        Bliebe die Zeile der vorigen stehen, bekaeme die naechste die gespeicherte
        Antwort oder den Wiederverwendungs-Fall - beides ein Befund ueber den
        Aufbau, nicht ueber den Code.
        """
        async with self._engine.begin() as connection:
            await connection.execute(_DELETE_ALL)
