# Ein Weg zur Datenbank — und die Middleware, die nie gelaufen ist

**Entschieden:** 2026-08-06, 15:00 — die in
[`2026-08-06-1330`](2026-08-06-1330-shared-kernel-neuschnitt.md) offen gebliebene Zusammenführung
der beiden Datenbank-Wege.

## Die Entscheidung

`src/main.py` hielt zwei Verbindungen zu **derselben** Datenbank: einen `asyncpg`-Pool für
Health-Check und Idempotency-Middleware (Tickets 0001/0006) und eine SQLAlchemy-`AsyncEngine` für
die Slices. Der Pool ist ersatzlos entfallen. Es gibt jetzt genau eine Engine im Prozess; sie
fährt denselben Treiber (`asyncpg`), nur über SQLAlchemy.

Das ist keine Geschmacksfrage. Zwei Pools bedeuten zwei Konfigurationen, zwei
Ausfall-Charakteristiken und einen Health-Check, der eine Verbindung prüft, die mit der
Verbindung der Anfragen nichts zu tun hat — er hätte „gesund" gemeldet, während jeder
Slice-Aufruf an einer erschöpften Engine hängt.

## Was der Umbau ans Licht gebracht hat

Beim Verdrahten fielen drei Fehler auf, von denen zwei bedeuten, dass **die Anwendung nicht
lauffähig war** und **die Idempotenz nie funktioniert hat**:

1. **Der Startup brach ab.** Der Lifespan rief `setup_idempotency_middleware(app)` auf, und das
   ruft `add_middleware`. Starlette baut die Middleware-Kette beim ersten ASGI-Aufruf zusammen —
   und der erste ASGI-Aufruf *ist* der Lifespan-Aufruf. Jedes `add_middleware` im Startup kommt
   also zwangsläufig zu spät und wird mit `RuntimeError: Cannot add middleware after an
   application has started` quittiert. `uvicorn` hätte `lifespan.startup.failed` gemeldet und
   keine einzige Anfrage bedient. **Behoben:** Router, Exception-Handler und Middleware stehen auf
   Modulebene fest; der Lifespan legt nur noch Laufzeit-Ressourcen an. Die Middleware kann die
   Engine deshalb nicht im Konstruktor bekommen — sie liest sie je Anfrage aus `app.state`.

2. **Der Speicherpfad war unerreichbar.** `call_next` liefert unter `BaseHTTPMiddleware` eine
   Streaming-Antwort; die hat kein `.body`, sondern einen noch ungelesenen `body_iterator`. Die
   Zeile `json.loads(response.body...)` hätte mit `AttributeError` abgebrochen — es wurde nie ein
   Schlüssel gespeichert, also konnte auch nie einer treffen. **Behoben:** der Body wird
   eingesammelt, und weil er sich nur einmal lesen lässt, geht eine neue Antwort mit denselben
   Bytes hinaus.

3. **Der `TimeProvider` war Zierde.** Er wurde übergeben, gespeichert und nie benutzt; daneben
   stand ein direktes `datetime.now(tz=UTC)`. Jetzt liefert er den `created_utc`-Zeitstempel.

Alle drei sind **latente Fehler aus fertig gemergten Tickets** — dieselbe Familie wie das nicht
importierbare `main.py` aus [`2026-08-06-1245`](2026-08-06-1245-main-py-war-nicht-importierbar.md).

## Warum die Tests das nicht gesehen haben

Die Ursache ist in beiden Fällen dieselbe und lohnt das Festhalten: **die Tests haben genau das
weggelassen, worauf es ankam.**

- Die `db_pool`-Fixture in `tests/conftest.py` gab `None` zurück. Der einzige Test, der die
  Idempotenz wirklich prüft, begann mit `if db_pool is None: pytest.skip(...)` — er hat sich in
  jedem Lauf selbst übersprungen. Die verbleibenden Tests prüften ausschließlich die
  *Durchlass*-Fälle: kein Header, kein Nutzer, keine UUID. Also alles, was die Middleware **nicht**
  tut.
- Der Smoke-Test aus 1245 lud `main.py` nur. Fehler 1 sitzt aber nicht im Import, sondern im
  Startup.

Beides ist jetzt geschlossen: `tests/api/test_app_startup.py` fährt den Lifespan über das rohe
ASGI-Protokoll — denn nur dieser Aufruf baut die Middleware-Kette so auf wie `uvicorn` — und
`tests/shared_infrastructure/test_idempotency_api.py` läuft gegen die Testcontainers-Engine, mit
dem Treffer-Fall und der Prüfung, dass die Zeile mit allen Feldern wirklich in
`shared_kernel.idempotency_keys` steht.

**Eine Fixture, die `None` liefert, damit die Tests durchlaufen, ist kein Test-Double — sie ist
ein Ausschalter.** Wo ein Testfall ohne Ressource nichts prüfen kann, gehört die echte Ressource
her (die gibt es hier seit Ticket 0009) oder der Testfall gestrichen.

## Was das ausschließt

- Kein zweiter Verbindungsweg zur Datenbank. Braucht etwas Rohzugriff, holt es sich eine
  Verbindung aus der bestehenden Engine.
- Nichts, was zur *Gestalt* der Anwendung gehört — Router, Handler, Middleware — wird im Lifespan
  angehängt. Der Lifespan ist für Ressourcen da, nicht für Struktur.
