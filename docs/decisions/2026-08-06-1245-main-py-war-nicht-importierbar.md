# `main.py` war seit Ticket 0002 nicht importierbar — Wiederherstellung und Absicherung

**Entdeckt und behoben:** 2026-08-06, 12:45 — beim Verdrahten von Stufe 3 (Ticket 0011).

## Was der Fall war

Der Einstiegspunkt der Anwendung ließ sich nicht laden:

```
ModuleNotFoundError: No module named 'fastapi.middleware.base'
ModuleNotFoundError: No module named 'starlette.middleware.csrf'
```

Beide Importe gehören zu einer `RateLimitMiddleware` und einer `CSRFMiddleware`, die mit
`96b8f2c` („Fix security findings") eingeführt und mit **`4165fed` bewusst zurückgenommen**
wurden — die zugehörige Begründung steht in
[`2026-08-05-0936`](2026-08-05-0936-security-gate-triage-ticket-0001.md). Über den Merge von
`c30054d` (PR zu Ticket 0002, Branch vom Stand *vor* dem Revert) sind sie unbemerkt
zurückgekehrt.

Damit war die Anwendung ab diesem Merge nicht mehr startfähig: kein `docker compose up`, kein
Health-Endpoint aus Ticket 0001, keine der später gebauten Middleware jemals im Betrieb. Die CI
blieb durchgehend grün.

## Warum es niemand gemerkt hat

**Kein einziger Test hat `main.py` je geladen.** Lint und Formatprüfung arbeiten auf dem
Syntaxbaum und führen keine Importe aus; der import-linter baut den Importgraphen statisch. Ein
Modul, das nichts importiert, kann beliebig kaputt sein, ohne dass ein Werkzeug anschlägt — und
ausgerechnet der Einstiegspunkt wird von keinem anderen Modul importiert, sondern nur von
`uvicorn` beim Start.

Das ist die eigentliche Lektion: nicht der falsche Import, sondern dass die einzige Datei, deren
Ladbarkeit über Start oder Nicht-Start entscheidet, als einzige nie geladen wurde.

## Was getan wurde

1. Beide Middleware entfernt — das stellt den mit `4165fed` gewollten Zustand wieder her, es ist
   keine neue Sicherheitsentscheidung. Sollte Rate Limiting je gewünscht sein, ist es laut
   `2026-08-05-0936` ein eigener Cross-Cutting-Baustein im `shared_kernel` mit eigenem Ticket,
   nicht ad hoc in `main.py`. CSRF-Schutz ist für eine JWT-basierte JSON-Schnittstelle ohnehin
   gegenstandslos — er adressiert cookie-getragene Authentifizierung.
2. `tests/api/test_app_startup.py` als Smoke-Test: das Modul lädt, und die Anwendung kennt ihre
   Endpunkte. Geprüft wird gegen `app.openapi()["paths"]`, nicht gegen `app.routes` — FastAPI
   hängt eingebundene Router als Referenz ein, statt ihre Routen flachzuziehen.
3. Der Import darf weiterhin **ohne** Umgebungsvariablen gelingen; die Konfiguration wird erst im
   `lifespan` geprüft. Ein `SECRET_KEY`-Zwang auf Modulebene (ebenfalls aus `96b8f2c`) ist damit
   ebenfalls verschwunden — er hätte jedes Werkzeug, das das Modul nur laden will, an eine
   vollständige Umgebung gebunden, und genau daran wäre auch der Smoke-Test gescheitert.

## Offen

`main.py` hält jetzt **zwei** Wege zur selben Datenbank: den `asyncpg`-Pool für Health-Check und
Idempotency-Middleware (Tickets 0001/0006) und die SQLAlchemy-Engine für die Slices. Einer zu
viel; zusammenzuführen beim nächsten Anfassen von 0006, nicht hier — das wäre Umbau an fremdem
Ticket-Scope.
