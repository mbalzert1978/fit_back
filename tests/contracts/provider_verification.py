"""Ein Provider-Verifikationslauf, fluent zusammengesteckt.

Hier liegt die Mechanik, die kein Test lesen will: die App unter `uvicorn` in
einem Thread, der Verifier von `pact-python`, und die Bruecke, die die
State-Handler aus Pacts eigenem Thread zurueck auf die Event-Loop des Tests
holt. Ein Test sagt damit nur noch, **was** verifiziert wird:

    await (
        ProviderVerifikation.fuer("nutritrack-identity", identity_pact)
        .nur_pfade(PurePosixPath("/api/v1/identity/register"))
        .mit_state("Konto existiert", setup=konto.anlegen, teardown=konto.entfernen)
        .verifiziere(app, pact_ablage)
    )

Weder hier noch im Test wird eine Datei geoeffnet: den fertigen `Pact` und die
`Ablage`, die der Verifier zum Lesen braucht, reicht die `conftest.py` herein.
Sie ist die einzige Stelle, die `json` importiert und das Dateisystem anfasst.

Wiederverwendbar fuer die uebrigen fuenf Vertraege, sobald ihre Contexts gebaut
sind - jeder bekommt seinen eigenen Lauf unter seinem eigenen Provider-Namen.
"""

import asyncio
import contextlib
import threading
from collections.abc import AsyncGenerator, Awaitable, Callable, Collection, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal, Self, final

import uvicorn
from fastapi import FastAPI
from pact.verifier import Verifier

__all__ = ["Ablage", "Interaktion", "Pact", "ProviderVerifikation", "Zustand"]

type Arbeit = Callable[[], Awaitable[None]]
"""Was ein State-Handler zu tun hat - als Coroutine-Funktion, ohne Argumente."""

type Ablage = Callable[[Mapping[str, object]], Path]
"""Legt den abzuspielenden Pact ab und nennt die Datei.

`pact-python` liest seine Quelle vom Dateisystem - irgendwo muss der reduzierte
Pact also landen. Wo, entscheidet der Test ueber seine Fixture, nicht dieser
Baukasten.
"""

type Haelfte = Literal["setup", "teardown"]
"""Die beiden Haelften, mit denen Pact einen State-Handler ruft."""

_START_FRIST = 30.0
"""Sekunden, die die App zum Hochfahren hat, bevor der Lauf abbricht."""


def _als[T](wert: object, art: type[T], wo: str) -> T:
    """Nimm einen Wert aus einem Pact als das, was dort stehen muss.

    Was aus einer JSON-Datei kommt, ist zunaechst nur `object`. Statt das mit
    `Any` zu verwischen, faellt hier auf, wenn eine Pact-Datei anders gebaut ist
    als angenommen - mit dem Feldnamen im Fehlertext.
    """
    if not isinstance(wert, art):
        msg = f"Der Pact fuehrt unter {wo} kein {art.__name__}, sondern {type(wert).__name__}."
        raise TypeError(msg)
    return wert


@final
@dataclass(frozen=True, slots=True)
class Interaktion:
    """Eine Interaktion des Pacts - sie weiss selbst, wohin sie zeigt.

    `pfad` ist ein `PurePosixPath`, kein String und kein URL-Typ. Kein String,
    weil der Typ `/api/v1/x` und `/api/v1//x` gleich vergleicht, wo ein String
    zwei verschiedene Dinge saehe. `PurePosixPath` statt `Path`, damit unter
    Windows nicht die Backslash-Semantik hereinrutscht. Und kein URL-Typ, weil im
    Pact genau das steht, was der Name sagt - ein Pfad. Schema, Host und Query
    gibt es dort nicht; ein URL-Typ wuerde drei Felder modellieren, die leer
    bleiben, und die Frage aufwerfen, gegen welchen Host verglichen wird.

    `roh` bleibt mit, weil ein abgespielter Pact wieder eine Pact-Datei sein muss:
    was der Builder nicht liest, gibt er unveraendert zurueck.
    """

    beschreibung: str
    pfad: PurePosixPath
    roh: Mapping[str, object]

    @classmethod
    def von(cls, roh: Mapping[str, object]) -> "Interaktion":
        """Deute eine Interaktion aus dem Inhalt einer Pact-Datei."""
        anfrage = _als(roh["request"], Mapping, "request")
        return cls(
            _als(roh["description"], str, "description"),
            PurePosixPath(_als(anfrage["path"], str, "request.path")),
            roh,
        )

    def zeigt_auf(self, pfade: Collection[PurePosixPath]) -> bool:
        """Gehoert diese Interaktion zu einem dieser Endpunkte?"""
        return self.pfad in pfade


@final
@dataclass(frozen=True, slots=True)
class Pact:
    """Eine Pact-Datei, aufgeteilt in ihre Interaktionen und alles Uebrige."""

    kopf: Mapping[str, object]
    interaktionen: tuple[Interaktion, ...]

    @classmethod
    def von(cls, roh: Mapping[str, object]) -> "Pact":
        """Deute den eingelesenen Inhalt einer Pact-Datei.

        Die einzige Stelle, die die Form eines Pacts kennt - ab hier haengt alles
        an Namen statt an Schluessel-Ketten. Gelesen wird die Datei in der
        `conftest.py`; was hier ankommt, ist schon geparst.
        """
        return cls(
            kopf={name: wert for name, wert in roh.items() if name != "interactions"},
            interaktionen=tuple(
                map(Interaktion.von, _als(roh["interactions"], list, "interactions"))
            ),
        )

    def nur_auf(self, pfade: Collection[PurePosixPath]) -> "Pact":
        """Derselbe Pact, beschraenkt auf die Interaktionen dieser Endpunkte."""
        return Pact(self.kopf, tuple(i for i in self.interaktionen if i.zeigt_auf(pfade)))

    @property
    def inhalt(self) -> Mapping[str, object]:
        """Derselbe Pact wieder als das, was in einer Pact-Datei stuende."""
        return {**self.kopf, "interactions": [i.roh for i in self.interaktionen]}


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

    def __init__(self, provider: str, pact: Pact) -> None:
        """Beginne einen Lauf dieses Providers gegen diesen Pact."""
        self._provider = provider
        self._abzuspielen = pact
        self._zustaende: list[Zustand] = []

    @classmethod
    def fuer(cls, provider: str, pact: Pact) -> Self:
        """Beginne einen Lauf dieses Providers gegen diesen Pact.

        Beides zusammen, weil ein Lauf ohne Pact nichts ist, was man
        versehentlich starten koennen sollte.
        """
        return cls(provider, pact)

    def nur_pfade(self, *pfade: PurePosixPath) -> Self:
        """Beschraenke den Lauf auf die Interaktionen dieser Endpunkte.

        Abgespielt wird dann ein reduzierter Pact - eine Kopie, die nur die
        gewaehlten Interaktionen traegt. Die Datei des Stakeholders bleibt
        unberuehrt, und der Ausschluss haengt an dem, was das Ticket meint: dem
        Endpunkt. Nicht an Beschreibungstexten, die der Consumer jederzeit
        umformuliert.
        """
        gewaehlt = self._abzuspielen.nur_auf(pfade)
        if not gewaehlt.interaktionen:
            msg = f"Der Pact hat keine Interaktion auf {[str(p) for p in pfade]}."
            raise AssertionError(msg)
        self._abzuspielen = gewaehlt
        return self

    def mit_state(self, name: str, *, setup: Arbeit, teardown: Arbeit) -> Self:
        """Hinterlege den Handler fuer einen Provider-State des Pacts."""
        self._zustaende.append(Zustand(name, setup, teardown))
        return self

    async def verifiziere(self, asgi_app: FastAPI, ablage: Ablage) -> None:
        """Fahre die App hoch, spiele den Pact dagegen ab, raeume wieder ab.

        Faellt der Lauf durch, wirft `pact-python` - das ist das Testergebnis.
        """
        handler = _handler_auf(asyncio.get_running_loop())
        quelle = ablage(self._abzuspielen.inhalt)

        async with _laufende_app(asgi_app) as url:
            verifier = (
                Verifier(self._provider, host="127.0.0.1")
                .add_transport(url=url)
                .add_source(quelle)
                .state_handler({z.name: handler(z) for z in self._zustaende}, teardown=True)
                # Ein Pact ohne Interaktionen ist ein Fehler, kein gruener Lauf.
                .set_error_on_empty_pact(enabled=True)
            )
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
