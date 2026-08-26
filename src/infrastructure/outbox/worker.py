"""Worker: laesst den Relay schlafen, bis Postgres ihn weckt.

Ohne LISTEN/NOTIFY bliebe nur Polling, und dessen Intervall waere zugleich die
mittlere Zustellverzoegerung - kurz genug fuer "sofort" hiesse, die Datenbank
dauerhaft leer abzufragen. Der Worker haelt stattdessen eine eigene Verbindung
im LISTEN-Zustand: Postgres schiebt beim Commit des Publishers eine
Benachrichtigung, und erst die weckt den Relay.

Das Polling verschwindet damit nicht ganz, es wird zum **Sicherheitsnetz** -
`idle_wait_seconds` faengt eine verlorene Benachrichtigung (Verbindungsabriss)
und faellige Retries ab, die von sich aus niemand ankuendigt.
"""

import asyncio
import contextlib
import logging
from typing import final

from sqlalchemy.ext.asyncio import AsyncEngine

from src.infrastructure.outbox.outbox import OUTBOX_CHANNEL
from src.infrastructure.outbox.relay import OutboxRelay

__all__ = ["OutboxWorker"]

_logger = logging.getLogger(__name__)


@final
class OutboxWorker:
    """Laeuft dauerhaft und stellt Outbox-Events zu, sobald welche anfallen."""

    def __init__(
        self,
        engine: AsyncEngine,
        relay: OutboxRelay,
        idle_wait_seconds: float = 5.0,
    ) -> None:
        """Verdrahte Worker mit Datenbank und Relay."""
        self._engine = engine
        self._relay = relay
        self._idle_wait_seconds = idle_wait_seconds

    async def run(self) -> None:
        """Verarbeite Events, bis die Task abgebrochen wird.

        Beendet wird ueber `asyncio.CancelledError` - kein eigenes Stop-Flag,
        siehe `.rules/python/python-async.md`, "Cancellation fliesst nativ mit".
        """
        wakeup = asyncio.Event()

        # Eigene Verbindung, die nur lauscht: der Relay braucht seine
        # Transaktionen fuer sich, und eine Verbindung im LISTEN-Zustand darf
        # nicht gleichzeitig fuer Abfragen benutzt werden.
        # Als Name festgehalten, nicht inline: `remove_listener` identifiziert den
        # Callback ueber Objektgleichheit, und ein zweites Lambda mit gleichem
        # Rumpf ist ein anderes Objekt - es wuerde nichts entfernen.
        def on_notify(*_: object) -> None:
            wakeup.set()

        async with self._engine.connect() as listening:
            driver_connection = (await listening.get_raw_connection()).driver_connection
            if driver_connection is None:
                # Hinter der Verbindung steht keine DBAPI-Verbindung, also gibt
                # es hier kein LISTEN/NOTIFY. Das ist kein Startfehler: das
                # Polling in `_pump` ist ohnehin das Sicherheitsnetz (siehe
                # Modul-Docstring) und stellt weiter zu - nur mit
                # `idle_wait_seconds` als Zustellverzoegerung statt "sofort".
                # Verspaetete Zustellung schlaegt gar keine, deshalb laut melden
                # und degradiert weiterlaufen, statt den Relay abzuschalten.
                _logger.error(
                    "Outbox-Worker lauscht nicht auf %s: keine DBAPI-Verbindung hinter der "
                    "Engine. Zustellung laeuft nur ueber das Polling, bis zu %.0fs verzoegert.",
                    OUTBOX_CHANNEL,
                    self._idle_wait_seconds,
                )
                await self._pump(wakeup)
                return

            await driver_connection.add_listener(OUTBOX_CHANNEL, on_notify)
            _logger.info("Outbox-Worker lauscht auf %s", OUTBOX_CHANNEL)
            try:
                await self._pump(wakeup)
            finally:
                with contextlib.suppress(Exception):
                    await driver_connection.remove_listener(OUTBOX_CHANNEL, on_notify)

    async def _pump(self, wakeup: asyncio.Event) -> None:
        """Abwechselnd leerraeumen und warten."""
        while True:
            # Zuerst zuruecksetzen, dann leerraeumen: eine Benachrichtigung, die
            # waehrend des Leerraeumens eintrifft, bleibt so gesetzt und
            # verhindert, dass der naechste Durchlauf sich schlafen legt,
            # obwohl gerade etwas hereingekommen ist.
            wakeup.clear()
            while await self._relay.relay_due_events() > 0:
                pass
            with contextlib.suppress(TimeoutError):
                async with asyncio.timeout(self._idle_wait_seconds):
                    await wakeup.wait()
