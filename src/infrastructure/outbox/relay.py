"""Relay: holt faellige Events aus der Outbox und uebergibt sie den Registrierten.

Die Kernaussage steckt in einer einzigen Query-Zeile - `FOR UPDATE SKIP LOCKED`.
Sie sperrt die geholten Zeilen fuer die Dauer der Transaktion und laesst jede
weitere Worker-Instanz die bereits gesperrten **ueberspringen** statt auf sie zu
warten. Damit sieht kein Event zwei Worker gleichzeitig, ohne dass irgendwo ein
globales Lock, eine Leader-Wahl oder ein Broker noetig waere.

Wen der Relay beliefert, gibt er nicht vor: er schlaegt den Event-Typ in der
`EventRegistry` nach. Die Contexts tragen sich dort beim Aufbau ein, der Relay
kennt keinen von ihnen.
"""

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import final
from uuid import UUID

from sqlalchemy import RowMapping, TextClause, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from src.contexts.shared_kernel.events import DeliveredEvent, EventRegistry, JsonValue
from src.contexts.shared_kernel.time_provider import TimeProvider
from src.contexts.shared_kernel.timestamp import Timestamp

__all__ = [
    "OutboxRelay",
    "RelayConfig",
]

_logger = logging.getLogger(__name__)


@final
@dataclass(frozen=True, slots=True)
class RelayConfig:
    """Stellschrauben des Relays."""

    batch_size: int = 32
    """Wie viele Events eine Transaktion hoechstens beansprucht."""

    max_attempts: int = 5
    """Nach so vielen erfolglosen Versuchen wird ein Event liegengelassen (Dead Letter)."""

    backoff_base_seconds: int = 1
    """Wartezeit vor dem zweiten Versuch; danach verdoppelnd."""

    backoff_cap_seconds: int = 300
    """Obergrenze des Backoffs, damit er nicht ins Unermessliche waechst."""


# `payload::text`: asyncpg liefert `jsonb` je nach Codec als `str` oder als
# bereits geparstes Objekt. Der explizite Cast macht daraus einen einzigen,
# vorhersagbaren Fall - immer `str`, immer selbst geparst.
_CLAIM_DUE: TextClause = text("""
    SELECT id, event_type, payload::text AS payload, occurred_at, attempts
    FROM shared_kernel.outbox
    WHERE processed_at IS NULL
      AND failed_at IS NULL
      AND next_attempt_at <= :now
    ORDER BY id
    FOR UPDATE SKIP LOCKED
    LIMIT :batch_size
""")

_MARK_DELIVERED: TextClause = text("""
    UPDATE shared_kernel.outbox
    SET processed_at = :now, attempts = :attempts, last_error = NULL
    WHERE id = :id
""")

_MARK_RETRY: TextClause = text("""
    UPDATE shared_kernel.outbox
    SET attempts = :attempts, last_error = :last_error, next_attempt_at = :next_attempt_at
    WHERE id = :id
""")

_MARK_FAILED: TextClause = text("""
    UPDATE shared_kernel.outbox
    SET attempts = :attempts, last_error = :last_error, failed_at = :now
    WHERE id = :id
""")


@final
class OutboxRelay:
    """Stellt faellige Outbox-Events an die registrierten Handler zu."""

    def __init__(
        self,
        engine: AsyncEngine,
        registry: EventRegistry,
        clock: TimeProvider,
        config: RelayConfig | None = None,
    ) -> None:
        """Verdrahte Relay mit Datenbank, Registrierungen und Uhr."""
        self._engine = engine
        self._registry = registry
        self._clock = clock
        self._config = config or RelayConfig()

    async def relay_due_events(self) -> int:
        """Verarbeite hoechstens einen Batch und gib zurueck, wie viele Events beansprucht wurden.

        `0` heisst: gerade nichts faellig. Der Aufrufer (`OutboxWorker`) nimmt das
        als Signal, sich schlafen zu legen, statt weiterzudrehen.

        Zustellung und Statuswechsel liegen in **einer** Transaktion. Bricht der
        Prozess dazwischen ab, verfaellt die Sperre und das Event ist wieder
        faellig - deshalb at-least-once und nicht exactly-once.
        """
        now = self._clock.now()
        async with self._engine.begin() as connection:
            claimed = (
                (
                    await connection.execute(
                        _CLAIM_DUE,
                        {"now": now.unix_seconds, "batch_size": self._config.batch_size},
                    )
                )
                .mappings()
                .all()
            )
            for row in claimed:
                await self._deliver_one(connection, row, now)
        return len(claimed)

    async def _deliver_one(
        self,
        connection: AsyncConnection,
        row: RowMapping,
        now: Timestamp,
    ) -> None:
        """Stelle ein Event zu und schreibe das Ergebnis in dieselbe Transaktion."""
        event_id: UUID = row["id"]
        attempt = int(row["attempts"]) + 1
        event = DeliveredEvent(
            event_id=event_id,
            event_type=str(row["event_type"]),
            payload=self._decode_payload(row["payload"]),
            occurred_at=Timestamp(int(row["occurred_at"])),
            attempt=attempt,
        )

        try:
            # Scheitert ein Handler, gilt das **ganze** Event als nicht
            # zugestellt und wird spaeter erneut allen Handlern angeboten.
            # Deshalb steht in `EventHandler`, dass eine Reaktion idempotent
            # sein muss - ein bereits erfolgreicher Handler laeuft dann noch
            # einmal. Die Alternative waere, Zustellzustand je Handler zu
            # fuehren; das lohnt sich erst, wenn ein Event tatsaechlich viele
            # teure Reaktionen hat.
            for handler in self._registry.handlers_for(event.event_type):
                await handler.handle(event)
        except Exception as failure:  # noqa: BLE001 -- ein Consumer darf beliebig scheitern
            await self._record_failure(connection, event_id, attempt, failure, now)
            return

        await connection.execute(
            _MARK_DELIVERED,
            {"id": event_id, "now": now.unix_seconds, "attempts": attempt},
        )

    async def _record_failure(
        self,
        connection: AsyncConnection,
        event_id: UUID,
        attempt: int,
        failure: Exception,
        now: Timestamp,
    ) -> None:
        """Halte einen Fehlversuch fest - als Faelligkeit, nicht als Wartezeit.

        Der Backoff landet in `next_attempt_at`. Ihn hier abzuwarten wuerde
        bedeuten, unter gehaltenen Row-Locks zu schlafen und damit genau den
        Durchsatz zu blockieren, den `SKIP LOCKED` gerade freigibt.
        """
        last_error = f"{type(failure).__name__}: {failure}"
        if attempt >= self._config.max_attempts:
            _logger.error(
                "Outbox-Event %s nach %d Versuchen aufgegeben: %s", event_id, attempt, last_error
            )
            await connection.execute(
                _MARK_FAILED,
                {
                    "id": event_id,
                    "attempts": attempt,
                    "last_error": last_error,
                    "now": now.unix_seconds,
                },
            )
            return

        delay = min(
            self._config.backoff_base_seconds * 2 ** (attempt - 1),
            self._config.backoff_cap_seconds,
        )
        _logger.warning(
            "Outbox-Event %s fehlgeschlagen (Versuch %d), naechster in %ds: %s",
            event_id,
            attempt,
            delay,
            last_error,
        )
        await connection.execute(
            _MARK_RETRY,
            {
                "id": event_id,
                "attempts": attempt,
                "last_error": last_error,
                "next_attempt_at": now.unix_seconds + delay,
            },
        )

    @staticmethod
    def _decode_payload(raw: object) -> Mapping[str, JsonValue]:
        """Lies die Nutzlast aus dem `payload::text` der Claim-Query."""
        decoded = json.loads(str(raw))
        if not isinstance(decoded, dict):
            msg = f"Outbox-Payload ist kein JSON-Objekt, sondern {type(decoded).__name__}"
            raise TypeError(msg)
        return decoded
