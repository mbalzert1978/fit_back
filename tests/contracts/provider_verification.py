"""Ein Provider-Verifikationslauf, fluent zusammengesteckt.

Hier liegt die Mechanik, die kein Test lesen will: die App unter `uvicorn` in
einem Thread, der Verifier von `pact-python`, und die Bruecke, die die
State-Handler aus Pacts eigenem Thread zurueck auf die Event-Loop des Tests
holt. Ein Test sagt damit nur noch, **was** verifiziert wird:

    await (
        ProviderVerifikation.fuer("nutritrack-identity")
        .mit_vertrag(PACT_DATEI)
        .nur_interaktionen(r"^Registrierung ")
        .mit_state("Konto existiert", setup=konto.anlegen, teardown=konto.entfernen)
        .verifiziere(app)
    )

Wiederverwendbar fuer die uebrigen fuenf Vertraege, sobald ihre Contexts gebaut
sind - jeder bekommt seinen eigenen Lauf unter seinem eigenen Provider-Namen.
"""

import asyncio
import threading
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Literal, Self

import uvicorn
from pact.verifier import Verifier

__all__ = ["ProviderVerifikation", "Zustand"]

type Arbeit = Callable[[], Awaitable[None]]
"""Was ein State-Handler zu tun hat - als Coroutine-Funktion, ohne Argumente."""


class Zustand:
    """Ein Provider-State: was ihn herstellt, und was ihn wieder aufraeumt.

    Getrennt gehalten, weil Pact beides getrennt aufruft und der Teardown der
    wichtigere Teil ist: er entscheidet, ob zwei Interaktionen mit demselben
    State einander stoeren.
    """

    def __init__(self, name: str, setup: Arbeit, teardown: Arbeit) -> None:
        """Nimm den Namen aus dem Vertrag und die beiden Haelften entgegen."""
        self.name = name
        self._setup = setup
        self._teardown = teardown

    def als_handler(self, auf_schleife: "Schleifenbruecke") -> Callable[..., None]:
        """Uebersetze in den synchronen Handler, den `pact-python` erwartet."""

        def handler(action: Literal["setup", "teardown"]) -> None:
            auf_schleife(self._setup if action == "setup" else self._teardown)

        return handler


class Schleifenbruecke:
    """Fuehrt Coroutinen auf einer fremden, laufenden Event-Loop aus.

    Pact ruft die State-Handler aus dem Thread seines eigenen kleinen
    HTTP-Servers heraus auf. Die Datenbank-Engine des Tests gehoert aber dessen
    Event-Loop; von einem fremden Thread aus benutzt, faellt asyncpg um. Diese
    Bruecke reicht die Arbeit zurueck - moeglich, weil `verifiziere()` den
    Verifier seinerseits in einem Thread laufen laesst und die Loop des Tests
    damit frei ist.
    """

    def __init__(self, schleife: asyncio.AbstractEventLoop) -> None:
        """Merke dir die Loop, auf der die Arbeit zu laufen hat."""
        self._schleife = schleife

    def __call__(self, arbeit: Arbeit) -> None:
        """Fuehre die Arbeit dort aus und warte auf ihr Ende."""
        asyncio.run_coroutine_threadsafe(arbeit(), self._schleife).result()


class ProviderVerifikation:
    """Der schrittweise Aufbau eines Verifikationslaufs."""

    def __init__(self, provider: str) -> None:
        """Beginne einen Lauf fuer diesen Provider-Namen."""
        self._provider = provider
        self._vertrag: Path | None = None
        self._filter: str | None = None
        self._zustaende: list[Zustand] = []

    @classmethod
    def fuer(cls, provider: str) -> Self:
        """Beginne einen Lauf fuer den Provider dieses Namens."""
        return cls(provider)

    def mit_vertrag(self, datei: Path) -> Self:
        """Verifiziere gegen diese Vertragsdatei."""
        self._vertrag = datei
        return self

    def nur_interaktionen(self, beschreibungsmuster: str) -> Self:
        """Beschraenke den Lauf auf Interaktionen, deren Beschreibung passt.

        So bleiben noch ungebaute Endpunkte draussen, ohne dass jemand die
        Vertragsdatei anfassen muesste: das Aufmachen ist spaeter eine Aenderung
        an genau einem Ausdruck.
        """
        self._filter = beschreibungsmuster
        return self

    def mit_state(self, name: str, *, setup: Arbeit, teardown: Arbeit) -> Self:
        """Hinterlege den Handler fuer einen Provider-State des Vertrags."""
        self._zustaende.append(Zustand(name, setup, teardown))
        return self

    async def verifiziere(self, asgi_app: object) -> None:
        """Fahre die App hoch, spiele den Vertrag dagegen ab, raeume wieder ab.

        Faellt der Lauf durch, wirft `pact-python` - das ist das Testergebnis.
        """
        if self._vertrag is None:
            msg = "Ohne `mit_vertrag(...)` gibt es nichts zu verifizieren."
            raise ValueError(msg)

        auf_schleife = Schleifenbruecke(asyncio.get_running_loop())
        async with _laufende_app(asgi_app) as url:
            verifier = (
                Verifier(self._provider, host="127.0.0.1")
                .add_transport(url=url)
                .add_source(self._vertrag)
                .state_handler(
                    {z.name: z.als_handler(auf_schleife) for z in self._zustaende},
                    teardown=True,
                )
                # Greift der Filter ins Leere, ist das ein Fehler - kein gruener Lauf.
                .set_error_on_empty_pact(enabled=True)
            )
            if self._filter is not None:
                verifier.filter(self._filter)

            # Im Thread, damit die Loop des Tests fuer die State-Handler frei bleibt.
            await asyncio.to_thread(verifier.verify)


class _laufende_app:  # noqa: N801 -- als Kontextmanager benutzt, nicht als Typ
    """Haelt die App unter `uvicorn` am Laufen und nennt ihre URL."""

    def __init__(self, asgi_app: object) -> None:
        # Port 0: das Betriebssystem sucht einen freien und nennt ihn ueber den
        # Socket zurueck. Ein selbst gewuerfelter Port waere zwischen Wahl und
        # `bind()` fuer andere frei.
        self._server = uvicorn.Server(
            uvicorn.Config(asgi_app, host="127.0.0.1", port=0, log_level="warning")
        )
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    async def __aenter__(self) -> str:
        self._thread.start()
        while not self._server.started:
            # Auf `is_alive()` mitwarten, nicht nur auf `started`: bricht der
            # Start ab (fehlende Konfiguration etwa), setzt uvicorn `started`
            # nie - und ein blosses `while not started` haengt dann fuer immer,
            # statt den Fehler zu zeigen.
            if not self._thread.is_alive():
                msg = "Die App ist beim Start abgebrochen - siehe die Ausgabe von uvicorn."
                raise RuntimeError(msg)
            await asyncio.sleep(0.05)
        port = self._server.servers[0].sockets[0].getsockname()[1]
        return f"http://127.0.0.1:{port}"

    async def __aexit__(self, *_: object) -> None:
        self._server.should_exit = True
        await asyncio.to_thread(self._thread.join, 10)
