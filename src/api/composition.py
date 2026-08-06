"""Composition Root: die eine Stelle, an der die Anwendung zusammengesteckt wird.

Alles darunter nimmt seine Mitspieler per Konstruktor entgegen und weiss nicht,
woher sie kommen. Hier ist der einzige Ort, der beides kennt - die konkrete
Infrastruktur und die Nahten, die sie erfuellt.

Zwei Lebensdauern liegen hier nebeneinander und duerfen nicht verwechselt werden:

- **Prozess**: Engine, `EventRegistry`, Relay-Worker. Einmal beim Start.
- **Anfrage**: die Transaktion. Genau eine je Vorgang, damit Aggregate-Write und
  Outbox-Zeile gemeinsam sichtbar werden oder gar nicht.
"""

import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from src.contexts.shared_kernel.events import EventRegistry
from src.contexts.shared_kernel.time_provider import SystemTimeProvider
from src.infrastructure.outbox import OutboxRelay, OutboxWorker

__all__ = [
    "build_engine",
    "build_event_registry",
    "request_transaction",
    "run_outbox_worker",
]

_logger = logging.getLogger(__name__)


def build_engine(database_url: str) -> AsyncEngine:
    """Baue die SQLAlchemy-Engine fuer den Prozess."""
    return create_async_engine(database_url, pool_pre_ping=True)


def build_event_registry() -> EventRegistry:
    """Baue die Registrierungen der Event-Konsumenten.

    Aktuell leer: `register_user` ist reiner Produzent, und die reagierenden
    Slices - Goals (Ticket 0018) und Diary (0026) - existieren noch nicht. Ein
    Ereignis ohne Reaktion gilt als erledigt; der Relay raeumt es also weg. Das
    ist beabsichtigt und kein Datenverlust: es gibt nichts, was damit geschehen
    sollte.

    Sobald ein Konsument entsteht, kommt hier eine Zeile der Form
    `registry.register(UserRegistered, handler)` hinzu - und **nur** hier.
    """
    return EventRegistry()


async def request_transaction(request: Request) -> AsyncGenerator[AsyncConnection]:
    """Oeffne genau eine Transaktion je Anfrage und committe sie am Ende.

    Kein `rollback` im Fehlerfall: verlaesst der Ablauf den Block ueber eine
    Exception, wird nie committet und die Verbindung beim Schliessen verworfen -
    nichts wird persistiert (.rules/python/python-data-access.md, "eine Session
    *ist* bereits eine Unit of Work").
    """
    engine: AsyncEngine = request.app.state.engine
    async with engine.connect() as connection:
        await connection.begin()
        yield connection
        await connection.commit()


@contextlib.asynccontextmanager
async def run_outbox_worker(engine: AsyncEngine, registry: EventRegistry) -> AsyncGenerator[None]:
    """Halte den Relay-Worker fuer die Lebensdauer der Anwendung am Laufen.

    Beendet wird ueber `Task.cancel()`; der Worker faengt das nicht ab, sondern
    laesst es propagieren und schliesst dabei seine LISTEN-Verbindung
    (.rules/python/python-async.md, "Cancellation fliesst nativ mit").
    """
    worker = OutboxWorker(engine, OutboxRelay(engine, registry, SystemTimeProvider()))
    running = asyncio.create_task(worker.run())
    try:
        yield
    finally:
        running.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await running
        _logger.info("Outbox-Worker beendet")
