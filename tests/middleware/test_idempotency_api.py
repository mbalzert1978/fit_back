"""Integrationstests der Idempotency-Key-Middleware gegen eine echte Datenbank.

Diese Datei lief bisher gegen eine `db_pool`-Fixture, die `None` zurueckgab -
der eine Test, auf den es ankommt (zweiter Aufruf mit demselben Schluessel
liefert die gespeicherte Antwort), hat sich damit selbst uebersprungen. Er laeuft
jetzt gegen die Testcontainers-Engine, dieselbe, die auch die Slices benutzen.
"""

import json
from collections.abc import AsyncGenerator, Awaitable, Callable
from uuid import UUID, uuid7

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from src.api.exception_handlers import register_exception_handlers
from src.api.i18n import create_resources
from src.api.identity import register_user_router
from src.contexts.shared_kernel.time_provider import FakeTimeProvider, SystemTimeProvider
from src.middleware.idempotency import (
    ANONYMOUS_USER_ID,
    IdempotencyKeyMiddleware,
    calculate_request_hash,
)
from src.middleware.response_envelope import ResponseEnvelopeMiddleware
from src.settings import Settings, get_settings

pytestmark = pytest.mark.asyncio


class _StubAuthMiddleware(BaseHTTPMiddleware):
    """Setzt eine feste `user_id` - die Idempotenz haengt an ihr."""

    def __init__(self, app: ASGIApp, user_id: UUID) -> None:
        super().__init__(app)
        self._user_id = user_id

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.user_id = self._user_id
        return await call_next(request)


def _build_app(engine: AsyncEngine, user_id: UUID | None) -> FastAPI:
    """Baue eine App mit einem Dummy-Endpunkt hinter der Middleware.

    `user_id=None` laesst die Stub-Auth weg und bildet damit den
    unauthentifizierten Fall ab.

    Reihenfolge: `add_middleware` schiebt jeweils nach vorn, die zuletzt
    hinzugefuegte Middleware laeuft also **aussen**. Die Auth muss aussen
    liegen, sonst sieht die Idempotenz-Pruefung noch keine `user_id`.
    """
    app = FastAPI()
    app.state.resources = create_resources()

    @app.post("/api/v1/test-idempotency")
    async def create() -> JSONResponse:
        return JSONResponse(status_code=201, content={"id": str(uuid7()), "data": "angelegt"})

    @app.put("/api/v1/test-idempotency")
    async def update() -> JSONResponse:
        return JSONResponse(status_code=200, content={"updated": True})

    @app.get("/api/v1/test-idempotency")
    async def read() -> JSONResponse:
        return JSONResponse(status_code=200, content={"data": "gelesen"})

    @app.post("/api/v1/mit-kopfzeilen")
    async def mit_kopfzeilen() -> JSONResponse:
        return JSONResponse(
            status_code=201,
            content={"id": "fest"},
            headers={
                "Location": "/api/v1/identity/me",
                "Content-Language": "de",
                # Traegt keine Aussage ueber das Ergebnis und darf deshalb nicht
                # mitwandern - Tage spaeter wiederholt waere er schlicht falsch.
                "Date": "Mon, 01 Jan 2001 00:00:00 GMT",
            },
        )

    @app.post("/api/v1/abgelehnt")
    async def abgelehnt() -> JSONResponse:
        return JSONResponse(status_code=400, content={"fehler": "ungueltig"})

    @app.post("/api/v1/kaputt")
    async def kaputt() -> JSONResponse:
        msg = "etwas ging schief"
        raise RuntimeError(msg)

    app.add_middleware(IdempotencyKeyMiddleware, time_provider=FakeTimeProvider())
    if user_id is not None:
        app.add_middleware(_StubAuthMiddleware, user_id=user_id)
    app.state.engine = engine
    return app


@pytest_asyncio.fixture
async def clean_idempotency_keys(postgres_engine: AsyncEngine) -> AsyncGenerator[AsyncEngine]:
    """Leere die Tabelle vor und nach jedem Test."""
    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE shared_kernel.idempotency_keys"))
    yield postgres_engine
    async with postgres_engine.begin() as connection:
        await connection.execute(text("TRUNCATE shared_kernel.idempotency_keys"))


async def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_zweiter_aufruf_liefert_die_gespeicherte_antwort(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """Der Kern des Tickets: gleicher Schluessel, gleiche Antwort - Statuscode inbegriffen."""
    app = _build_app(clean_idempotency_keys, user_id=uuid7())
    key = str(uuid7())

    async with await _client(app) as client:
        first = await client.post("/api/v1/test-idempotency", headers={"Idempotency-Key": key})
        second = await client.post("/api/v1/test-idempotency", headers={"Idempotency-Key": key})

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json() == first.json()


async def test_der_eintrag_traegt_alle_geforderten_felder(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """`shared_kernel.idempotency_keys` bekommt Schluessel, Nutzer, Hash, Body und Zeitpunkt."""
    user_id = uuid7()
    app = _build_app(clean_idempotency_keys, user_id=user_id)
    key = uuid7()

    async with await _client(app) as client:
        await client.post("/api/v1/test-idempotency", headers={"Idempotency-Key": str(key)})

    async with clean_idempotency_keys.connect() as connection:
        found = await connection.execute(
            text("""
                SELECT key, user_id, request_hash, response_body, created_utc
                FROM shared_kernel.idempotency_keys
            """)
        )
        row = found.mappings().one()

    assert row["key"] == key
    assert row["user_id"] == user_id
    assert len(row["request_hash"]) == 64
    assert "angelegt" in row["response_body"]
    # FakeTimeProvider steht auf 2000-01-01 - der Zeitpunkt kommt aus dem
    # TimeProvider, nicht aus einem direkten Uhrablesen in der Middleware.
    assert row["created_utc"].year == 2000


async def test_verschiedene_schluessel_stoeren_sich_nicht(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    app = _build_app(clean_idempotency_keys, user_id=uuid7())

    async with await _client(app) as client:
        first = await client.post(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": str(uuid7())}
        )
        second = await client.post(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": str(uuid7())}
        )

    assert (first.status_code, second.status_code) == (201, 201)
    assert first.json() != second.json()


async def test_ohne_schluessel_geht_die_anfrage_durch(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    app = _build_app(clean_idempotency_keys, user_id=uuid7())

    async with await _client(app) as client:
        response = await client.post("/api/v1/test-idempotency")

    assert response.status_code == 201


async def test_ohne_angemeldeten_nutzer_greift_der_schluessel_trotzdem(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """Ohne `user_id` tritt `ANONYMOUS_USER_ID` ein - der Schluessel wird belegt.

    Die Registrierung hat keinen angemeldeten Nutzer und braucht die Idempotenz
    gerade dort: zweimal abgeschickt entstuende sonst ein zweites Konto (#95).
    """
    app = _build_app(clean_idempotency_keys, user_id=None)
    key = str(uuid7())

    async with await _client(app) as client:
        first = await client.post("/api/v1/test-idempotency", headers={"Idempotency-Key": key})
        second = await client.post("/api/v1/test-idempotency", headers={"Idempotency-Key": key})

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json() == first.json()

    async with clean_idempotency_keys.connect() as connection:
        stored = await connection.scalar(
            text("SELECT user_id FROM shared_kernel.idempotency_keys WHERE key = :key"),
            {"key": key},
        )
    assert stored == ANONYMOUS_USER_ID


async def test_ungueltige_uuid_im_header_geht_durch(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    app = _build_app(clean_idempotency_keys, user_id=uuid7())

    async with await _client(app) as client:
        response = await client.post(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": "kein-uuid"}
        )

    assert response.status_code == 201


async def test_get_wird_nicht_behandelt(clean_idempotency_keys: AsyncEngine) -> None:
    """Nur POST und PUT sind idempotenzpflichtig."""
    app = _build_app(clean_idempotency_keys, user_id=uuid7())

    async with await _client(app) as client:
        response = await client.get(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": str(uuid7())}
        )

    assert response.status_code == 200


async def test_derselbe_schluessel_mit_anderem_body_wird_abgelehnt(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """409 statt der Antwort von vorhin - genau dafuer steht der request_hash in der Tabelle.

    Ohne diesen Vergleich bekaeme der Aufrufer stillschweigend das Ergebnis
    seiner ERSTEN Anfrage und hielte seinen zweiten, voellig anderen Vorgang
    fuer erledigt.
    """
    app = _build_app(clean_idempotency_keys, user_id=uuid7())
    key = str(uuid7())

    async with await _client(app) as client:
        first = await client.post(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": key}, json={"menge": 1}
        )
        second = await client.post(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": key}, json={"menge": 999}
        )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.headers["content-type"].startswith("application/problem+json")
    assert second.json()["type"].endswith("/idempotency-key-reused")


async def test_der_schluessel_eines_anderen_nutzers_ist_belegt(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """409 - und die Antwort verraet nicht, dass der Schluessel jemand anderem gehoert.

    Derselbe Ausgang wie beim abweichenden Body: waeren die beiden Faelle
    unterscheidbar, liesse sich damit die Schluesselvergabe fremder Nutzer
    abtasten.
    """
    key = str(uuid7())
    async with await _client(_build_app(clean_idempotency_keys, user_id=uuid7())) as erster:
        await erster.post("/api/v1/test-idempotency", headers={"Idempotency-Key": key})

    async with await _client(_build_app(clean_idempotency_keys, user_id=uuid7())) as zweiter:
        response = await zweiter.post("/api/v1/test-idempotency", headers={"Idempotency-Key": key})

    assert response.status_code == 409
    assert response.json()["type"].endswith("/idempotency-key-reused")


async def test_eine_laufende_anfrage_blockt_den_zweiten_versuch(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """409, solange die erste Anfrage noch keine Antwort hinterlassen hat.

    Der Zustand wird hier direkt gesetzt statt echt nebenlaeufig erzeugt: eine
    Reservierung ohne Antwort ist genau das, was eine noch laufende Anfrage
    hinterlaesst.
    """
    user_id = uuid7()
    key = uuid7()
    app = _build_app(clean_idempotency_keys, user_id=user_id)

    async with await _client(app) as client:
        # Den Hash so bilden, wie die Middleware ihn fuer diese Anfrage bildet -
        # sonst schlaegt der Body-Vergleich zu und der Test pruefte den
        # Wiederverwendungs-Fall statt den laufenden Erstversuch - beide 409,
        # unterscheidbar nur am `type`.
        request_hash = calculate_request_hash("POST", "/api/v1/test-idempotency", "")
        async with clean_idempotency_keys.begin() as connection:
            await connection.execute(
                text("""
                    INSERT INTO shared_kernel.idempotency_keys
                        (key, user_id, request_hash, response_body, created_utc)
                    VALUES (:key, :user_id, :request_hash, NULL, now())
                """),
                {"key": key, "user_id": user_id, "request_hash": request_hash},
            )

        response = await client.post(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": str(key)}
        )

    assert response.status_code == 409
    assert response.json()["type"].endswith("/request-in-progress")


async def test_eine_abgelehnte_anfrage_gibt_den_schluessel_frei(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """Ein 400 hinterlaesst nichts Wiederholbares - der Schluessel darf nicht blockiert bleiben."""
    app = _build_app(clean_idempotency_keys, user_id=uuid7())
    key = str(uuid7())

    async with await _client(app) as client:
        first = await client.post("/api/v1/abgelehnt", headers={"Idempotency-Key": key})
        second = await client.post("/api/v1/abgelehnt", headers={"Idempotency-Key": key})

    assert (first.status_code, second.status_code) == (400, 400)
    async with clean_idempotency_keys.connect() as connection:
        stored = await connection.scalar(
            text("SELECT count(*) FROM shared_kernel.idempotency_keys")
        )
    assert stored == 0


async def test_eine_gescheiterte_anfrage_gibt_den_schluessel_frei(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    app = _build_app(clean_idempotency_keys, user_id=uuid7())
    key = str(uuid7())

    async with await _client(app) as client:
        with pytest.raises(RuntimeError):
            await client.post("/api/v1/kaputt", headers={"Idempotency-Key": key})

    async with clean_idempotency_keys.connect() as connection:
        stored = await connection.scalar(
            text("SELECT count(*) FROM shared_kernel.idempotency_keys")
        )
    assert stored == 0


async def test_put_wird_ebenfalls_zwischengespeichert(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    app = _build_app(clean_idempotency_keys, user_id=uuid7())
    key = str(uuid7())

    async with await _client(app) as client:
        await client.put("/api/v1/test-idempotency", headers={"Idempotency-Key": key})
        second = await client.put("/api/v1/test-idempotency", headers={"Idempotency-Key": key})

    assert second.status_code == 200
    async with clean_idempotency_keys.connect() as connection:
        stored = await connection.scalar(
            text("SELECT count(*) FROM shared_kernel.idempotency_keys")
        )
    assert stored == 1


async def test_der_wiederverwendete_schluessel_nennt_die_sprache_der_antwort(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """409 traegt `Content-Language` - sonst geht die ausgehandelte Sprache verloren.

    Der Rumpf ist bereits uebersetzt; ohne den Header koennen Aufrufer und Caches
    nicht erkennen, in welcher Sprache er vorliegt, und ein Cache lieferte die
    englische Antwort spaeter an einen deutschen Aufrufer aus.
    """
    app = _build_app(clean_idempotency_keys, user_id=uuid7())
    key = str(uuid7())

    async with await _client(app) as client:
        await client.post(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": key}, json={"menge": 1}
        )
        auf_englisch = await client.post(
            "/api/v1/test-idempotency",
            headers={"Idempotency-Key": key, "Accept-Language": "en-US"},
            json={"menge": 999},
        )

    assert auf_englisch.status_code == 409
    assert auf_englisch.headers["content-language"] == "en-US"
    assert auf_englisch.json()["title"] == "Idempotency key already in use"


async def test_die_laufende_anfrage_nennt_die_sprache_der_antwort(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """Dasselbe fuer die 409 - beide Ausgaenge gehen durch dieselbe `_problem`."""
    app = _build_app(clean_idempotency_keys, user_id=uuid7())
    key = str(uuid7())

    async with clean_idempotency_keys.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO shared_kernel.idempotency_keys "
                "(key, user_id, request_hash, response_body, created_utc) "
                "VALUES (:key, :user_id, :hash, NULL, now())"
            ),
            {
                "key": key,
                "user_id": str(uuid7()),
                "hash": calculate_request_hash("POST", "/api/v1/test-idempotency", ""),
            },
        )

    async with await _client(app) as client:
        response = await client.post(
            "/api/v1/test-idempotency",
            headers={"Idempotency-Key": key, "Accept-Language": "en-US"},
        )

    assert response.status_code == 409
    assert response.headers["content-language"] == "en-US"


async def test_der_replay_traegt_die_vertragsrelevanten_kopfzeilen(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """`Location` und `Content-Language` gehoeren zur Antwort und werden wiederholt.

    Die beschreibenden Kopfzeilen der ersten Antwort dagegen nicht: `Date` gilt
    fuer den Zeitpunkt von damals, `Content-Length` fuer den Rumpf von damals.
    Wiederholt waeren sie eine Aussage ueber eine Antwort, die es nicht mehr gibt.
    """
    app = _build_app(clean_idempotency_keys, user_id=uuid7())
    key = str(uuid7())

    async with await _client(app) as client:
        first = await client.post("/api/v1/mit-kopfzeilen", headers={"Idempotency-Key": key})
        second = await client.post("/api/v1/mit-kopfzeilen", headers={"Idempotency-Key": key})

    assert (first.status_code, second.status_code) == (201, 201)
    assert second.headers["location"] == first.headers["location"]
    assert second.headers["content-language"] == first.headers["content-language"]
    assert "date" in first.headers
    assert "date" not in second.headers

    async with clean_idempotency_keys.connect() as connection:
        aufgezeichnet = await connection.scalar(
            text("SELECT response_headers FROM shared_kernel.idempotency_keys WHERE key = :key"),
            {"key": key},
        )
    assert set(json.loads(aufgezeichnet)) == {"location", "content-language"}


async def test_eine_zeile_ohne_aufgezeichneten_status_bleibt_bei_200(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """Vor `shared_005` angelegte Zeilen kennen weder Status noch Kopfzeilen.

    Sie sollen den Replay nicht zum Absturz bringen, sondern ihn auf sein altes
    Verhalten zurueckfallen lassen: 200 und keine Kopfzeilen.
    """
    user_id = uuid7()
    key = uuid7()
    app = _build_app(clean_idempotency_keys, user_id=user_id)

    async with clean_idempotency_keys.begin() as connection:
        await connection.execute(
            text("""
                INSERT INTO shared_kernel.idempotency_keys
                    (key, user_id, request_hash, response_body, created_utc)
                VALUES (:key, :user_id, :request_hash, :response_body, now())
            """),
            {
                "key": key,
                "user_id": user_id,
                "request_hash": calculate_request_hash("POST", "/api/v1/test-idempotency", ""),
                "response_body": '{"data": "von frueher"}',
            },
        )

    async with await _client(app) as client:
        response = await client.post(
            "/api/v1/test-idempotency", headers={"Idempotency-Key": str(key)}
        )

    assert response.status_code == 200
    assert response.json() == {"data": "von frueher"}
    assert "location" not in response.headers


async def test_der_umschlag_entsteht_beim_replay_nicht_doppelt(
    clean_idempotency_keys: AsyncEngine,
) -> None:
    """Der Replay wird genau einmal eingepackt - mit seiner *eigenen* `requestId`.

    Der Umschlag liegt ausserhalb der Idempotenz (`src/main.py`): gespeichert
    wird der nackte Rumpf, eingepackt wird auf dem Rueckweg. Laege er innen,
    stuende der Umschlag von gestern im `data` von heute - samt der `requestId`
    einer Anfrage, die laengst vorbei ist.
    """
    app = _build_app(clean_idempotency_keys, user_id=uuid7())
    app.add_middleware(ResponseEnvelopeMiddleware, time_provider=FakeTimeProvider())
    key = str(uuid7())

    async with await _client(app) as client:
        first = await client.post("/api/v1/mit-kopfzeilen", headers={"Idempotency-Key": key})
        second = await client.post("/api/v1/mit-kopfzeilen", headers={"Idempotency-Key": key})

    assert (first.status_code, second.status_code) == (201, 201)
    assert set(second.json()) == {"data", "meta"}
    assert second.json()["data"] == {"id": "fest"}
    assert second.json()["meta"]["requestId"] != first.json()["meta"]["requestId"]

    async with clean_idempotency_keys.connect() as connection:
        gespeichert = await connection.scalar(
            text("SELECT response_body FROM shared_kernel.idempotency_keys WHERE key = :key"),
            {"key": key},
        )
    assert json.loads(gespeichert) == {"id": "fest"}


@pytest_asyncio.fixture
async def register_client(
    clean_idempotency_keys: AsyncEngine,
) -> AsyncGenerator[AsyncClient]:
    """Die echte Registrierung hinter derselben Middleware-Kette wie in `src/main.py`."""
    async with clean_idempotency_keys.begin() as connection:
        await connection.execute(text("TRUNCATE identity.users CASCADE"))
        await connection.execute(text("TRUNCATE shared_kernel.outbox"))

    app = FastAPI()
    app.state.resources = create_resources()
    app.dependency_overrides[get_settings] = lambda: Settings(
        db_password="test", jwt_secret="t" * 32
    )
    # Reihenfolge wie in `src/main.py`: der Umschlag liegt ausserhalb der Idempotenz.
    app.add_middleware(IdempotencyKeyMiddleware, time_provider=FakeTimeProvider())
    app.add_middleware(ResponseEnvelopeMiddleware, time_provider=SystemTimeProvider())
    register_exception_handlers(app)
    app.include_router(register_user_router)
    app.state.engine = clean_idempotency_keys

    async with await _client(app) as http:
        yield http

    async with clean_idempotency_keys.begin() as connection:
        await connection.execute(text("TRUNCATE identity.users CASCADE"))
        await connection.execute(text("TRUNCATE shared_kernel.outbox"))


async def test_die_wiederholte_registrierung_antwortet_wie_der_erstaufruf(
    register_client: AsyncClient,
) -> None:
    """Zweimal `POST /register` unter demselben Schluessel: dieselbe Antwort.

    Statuscode, Rumpf und die vertragsrelevanten Kopfzeilen. Genau das ist der
    Sinn eines Idempotency-Keys - der Aufrufer, dem die erste Antwort verloren
    ging, darf nicht an der Antwort erkennen, dass er der zweite war.
    """
    key = str(uuid7())
    body = {
        "email": "markus@example.de",
        "password": "ein-langes-passwort",
        "displayName": "Markus",
        "locale": "de",
        "timeZoneId": "Europe/Berlin",
    }

    first = await register_client.post(
        "/api/v1/identity/register", json=body, headers={"Idempotency-Key": key}
    )
    second = await register_client.post(
        "/api/v1/identity/register", json=body, headers={"Idempotency-Key": key}
    )

    assert first.status_code == 201
    assert second.status_code == first.status_code
    assert second.json()["data"] == first.json()["data"]
    assert second.headers["location"] == first.headers["location"]
    assert second.headers["content-language"] == first.headers["content-language"]
