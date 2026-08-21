"""Ein Provider-Verifikationslauf, fluent zusammengesteckt.

Hier liegt die Mechanik, die kein Test lesen will: die App unter `uvicorn` in
einem Thread, der Verifier von `pact-python`, und die Bruecke, die die
State-Handler aus Pacts eigenem Thread zurueck auf die Event-Loop des Tests
holt. Ein Test sagt damit nur noch, **was** verifiziert wird:

    await (
        ProviderVerifikation.fuer("nutritrack-identity", PACT_DATEI)
        .nur_interaktionen(r"^Registrierung ")
        .mit_state("Konto existiert", setup=konto.anlegen, teardown=konto.entfernen)
        .verifiziere(app)
    )

Wiederverwendbar fuer die uebrigen fuenf Vertraege, sobald ihre Contexts gebaut
sind - jeder bekommt seinen eigenen Lauf unter seinem eigenen Provider-Namen.
"""

import asyncio
import contextlib
import json
import re
import threading
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Self, final

import uvicorn
from fastapi import FastAPI
from pact.verifier import Verifier

__all__ = ["ProviderVerifikation", "Zustand"]

type Arbeit = Callable[[], Awaitable[None]]
"""Was ein State-Handler zu tun hat - als Coroutine-Funktion, ohne Argumente."""

type Haelfte = Literal["setup", "teardown"]
"""Die beiden Haelften, mit denen Pact einen State-Handler ruft."""

_START_FRIST = 30.0
"""Sekunden, die die App zum Hochfahren hat, bevor der Lauf abbricht."""


@final
@dataclass(frozen=True, slots=True)
class Zustand:
    """Ein Provider-State: was ihn herstellt, und was ihn wieder aufraeumt.

    Beide Haelften getrennt gehalten, weil Pact sie getrennt ruft und der
    Teardown der wichtigere Teil ist: er entscheidet, ob zwei Interaktionen mit
    demselben State einander stoeren.
    """

    name: str
    setup: Arbeit
    teardown: Arbeit

    def haelfte(self, gerufene: Haelfte) -> Arbeit:
        """Die Haelfte, die Pact mit diesem Aufruf meint."""
        return self.setup if gerufene == "setup" else self.teardown


@final
class ProviderVerifikation:
    """Der schrittweise Aufbau eines Verifikationslaufs."""

    def __init__(self, provider: str, pact: Path) -> None:
        """Beginne einen Lauf dieses Providers gegen diese Pact-Datei."""
        self._provider = provider
        self._pact = pact
        self._filter: str | None = None
        self._zustaende: list[Zustand] = []

    @classmethod
    def fuer(cls, provider: str, pact: Path) -> Self:
        """Beginne einen Lauf dieses Providers gegen diese Pact-Datei.

        Beides zusammen, weil ein Lauf ohne Pact nichts ist, was man
        versehentlich starten koennen sollte.
        """
        return cls(provider, pact)

    def nur_interaktionen(self, beschreibungsmuster: str, *, erwartet: int) -> Self:
        """Beschraenke den Lauf auf Interaktionen, deren Beschreibung passt.

        So bleiben noch ungebaute Endpunkte draussen, ohne dass jemand die
        Pact-Datei anfassen muesste - sie bleibt genau so liegen, wie der
        Stakeholder sie abgelegt hat.

        `erwartet` ist keine Zierde: das Muster haengt an Beschreibungstexten,
        die der Consumer schreibt, und eine Umformulierung dort koennte es still
        danebengreifen lassen. Ein Lauf, der weniger verifiziert als angesagt,
        waere sonst gruen.
        """
        getroffen = self._passende_beschreibungen(beschreibungsmuster)
        if len(getroffen) != erwartet:
            msg = (
                f"Das Muster {beschreibungsmuster!r} trifft {len(getroffen)} Interaktionen, "
                f"angesagt waren {erwartet}: {sorted(getroffen)}"
            )
            raise AssertionError(msg)
        self._filter = beschreibungsmuster
        return self

    def _passende_beschreibungen(self, beschreibungsmuster: str) -> list[str]:
        interaktionen = json.loads(self._pact.read_text(encoding="utf-8"))["interactions"]
        muster = re.compile(beschreibungsmuster)
        return [i["description"] for i in interaktionen if muster.search(i["description"])]

    def mit_state(self, name: str, *, setup: Arbeit, teardown: Arbeit) -> Self:
        """Hinterlege den Handler fuer einen Provider-State des Vertrags."""
        self._zustaende.append(Zustand(name, setup, teardown))
        return self

    async def verifiziere(self, asgi_app: FastAPI) -> None:
        """Fahre die App hoch, spiele den Vertrag dagegen ab, raeume wieder ab.

        Faellt der Lauf durch, wirft `pact-python` - das ist das Testergebnis.
        """
        handler = _handler_auf(asyncio.get_running_loop())

        async with _laufende_app(asgi_app) as url:
            verifier = (
                Verifier(self._provider, host="127.0.0.1")
                .add_transport(url=url)
                .add_source(self._pact)
                .state_handler({z.name: handler(z) for z in self._zustaende}, teardown=True)
                # Greift der Filter ins Leere, ist das ein Fehler - kein gruener Lauf.
                .set_error_on_empty_pact(enabled=True)
            )
            if self._filter is not None:
                verifier.filter(self._filter)

            # Im Thread, damit die Loop des Tests fuer die State-Handler frei bleibt.
            await asyncio.to_thread(verifier.verify)


def _handler_auf(schleife: asyncio.AbstractEventLoop) -> Callable[[Zustand], Callable[..., None]]:
    """Baue aus einem `Zustand` den synchronen Handler, den `pact-python` erwartet.

    Pact ruft die State-Handler aus dem Thread seines eigenen kleinen
    HTTP-Servers heraus auf. Die Datenbank-Engine des Tests gehoert aber dessen
    Event-Loop; von einem fremden Thread aus benutzt, faellt asyncpg um. Der
    Umweg ueber `run_coroutine_threadsafe` reicht die Arbeit dorthin zurueck -
    moeglich, weil `verifiziere()` den Verifier seinerseits in einem Thread
    laufen laesst und die Loop des Tests damit frei ist.
    """

    def fuer(zustand: Zustand) -> Callable[..., None]:
        def handler(action: Haelfte) -> None:
            asyncio.run_coroutine_threadsafe(zustand.haelfte(action)(), schleife).result()

        return handler

    return fuer


@contextlib.asynccontextmanager
async def _laufende_app(asgi_app: FastAPI) -> AsyncGenerator[str]:
    """Halte die App unter `uvicorn` am Laufen und nenne ihre URL."""
    # Port 0: das Betriebssystem sucht einen freien und nennt ihn ueber den
    # Socket zurueck. Ein selbst gewuerfelter Port waere zwischen Wahl und
    # `bind()` fuer andere frei.
    server = uvicorn.Server(uvicorn.Config(asgi_app, host="127.0.0.1", port=0, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        async with asyncio.timeout(_START_FRIST):
            while not server.started:
                # Auf `is_alive()` mitwarten, nicht nur auf `started`: bricht der
                # Start ab - fehlende Konfiguration etwa -, setzt uvicorn
                # `started` nie, und ein blosses Warten verschwiege den Grund.
                if not thread.is_alive():
                    msg = "Die App ist beim Start abgebrochen - siehe die Ausgabe von uvicorn."
                    raise RuntimeError(msg)
                await asyncio.sleep(0.05)
        yield f"http://127.0.0.1:{_gebundener_port(server)}"
    finally:
        server.should_exit = True
        await asyncio.to_thread(thread.join, 10)


def _gebundener_port(server: uvicorn.Server) -> int:
    """Den Port nennen, den das Betriebssystem beim `bind()` vergeben hat."""
    return server.servers[0].sockets[0].getsockname()[1]
