# M0 — Projekt-Grundgerüst & Shared Kernel

**Bezug BACKEND.md:** Abschnitt 0 (Querschnitts-Regeln), technischer Rahmen aus
[`01-technical-decisions.md`](./01-technical-decisions.md).
**Voraussetzung:** —
**Fachlich:** keiner — rein technisches Fundament, ohne das kein Context lauffähig ist.

## Ziel

Ein leeres, aber lauffähiges Grundgerüst: FastAPI-Host startet, spricht mit Postgres (Docker
Compose), Bounded-Context-Ordnerstruktur steht, Cross-Cutting-Bausteine aus Abschnitt 0 sind
einmal implementiert und wiederverwendbar, CI-fähige Checks (`ruff`, `import-linter`, `pytest`)
laufen gegen ein leeres Projekt grün.

## Scope

- Repo-Layout gemäß `01-technical-decisions.md` (`src/contexts/`, `src/api/`, `src/shared_kernel/`).
- Docker Compose: `postgres`, `minio`, `app` (FastAPI via `uvicorn`); `docker compose up` bringt
  alles hoch, danach ist die API per `curl` erreichbar (Auftraggeber-Vorgabe: Docker Compose +
  curl als primärer manueller Testweg, zusätzlich zu automatisierten Tests).
- Alembic-Grundgerüst mit den 7 Schemas aus Abschnitt 0.18 (`identity`, `catalog`, `diary`,
  `recipes`, `goals`, `health`, `shared`) — leere Baseline-Migration je Schema.
- `shared_kernel`:
  - `Result[T, E]` (siehe `.rules/python/python-error-handling.md`).
  - `TimeProvider`-Protocol + Standardimplementierung (Abschnitt 0.12 — nie `datetime.utcnow()`
    direkt).
  - RFC-7807-`ProblemDetails`-Modell + FastAPI-Exception-Handler, der jeden erwarteten
    Domänenfehler auf `application/problem+json` abbildet (Abschnitt 0.6).
  - Idempotenz-Middleware/Decorator + Tabelle `shared.idempotency_keys` (Abschnitt 0.3, TTL 7
    Tage — Cleanup-Job separat vermerken, nicht Teil von M0 selbst, siehe „Nicht in Scope").
  - `IUserOwned`-Mixin/Protocol + SQLAlchemy-Basis, die jede Query zwingend auf `UserId` filtert
    (Abschnitt 0.5 — kein Context-übergreifendes „vergessen").
  - `UuidV7`-Helper (Abschnitt 0.19 — Client erzeugt Ids selbst; Server-Factories für interne Ids
    nutzen dieselbe Helper-Funktion).
  - `RowVersion`/Optimistic-Concurrency-Basis (`xmin`-Mapping, `If-Match`-Header-Auswertung,
    Abschnitt 0.13).
  - `de-DE`/`en-US`-Resource-Files-Mechanismus + `Accept-Language`-Auswertung (Abschnitt 0.9).
  - **Postgres-Outbox + Event-Relay** (`shared.outbox`-Tabelle, `SKIP LOCKED`/`LISTEN NOTIFY`-Relay
    analog zum OCR-Job aus M5) — Basis für alle asynchronen Integration Events zwischen Contexts,
    siehe „Cross-Context-Kommunikation" in `01-technical-decisions.md`.
- `.importlinter`-Contract-Datei: verbietet Importe zwischen `contexts/<a>` und `contexts/<b>`
  außer über `contexts/<b>/application/**` (keine Domain-/Infrastructure-Importe cross-context).
- `ruff`-Konfiguration in `pyproject.toml` (inkl. `ANN`-Regelsatz, siehe `.rules/python/README.md`).
- Test-Grundgerüst: `pytest`, `pytest-asyncio`, Testcontainers-Fixture für Postgres (für
  Integrationstests späterer Meilensteine wiederverwendbar).

## Nicht in Scope

- Kein fachlicher Endpunkt (kommt ab M1).
- Kein Idempotency-Key-TTL-Cleanup-Job (kann als eigenes kleines Ticket in M1 mitlaufen, sobald
  echte Schreib-Endpunkte existieren, die den Mechanismus nutzen).
- Kein OCR-Job-Queue-Mechanismus (Postgres `SKIP LOCKED`/`LISTEN NOTIFY`) — der ist Catalog/OCR-
  spezifisch und gehört in M5, auch wenn er infrastrukturell hier vorbereitet werden könnte;
  bewusst dorthin verschoben, um M0 klein und context-neutral zu halten.

## Cross-Cutting-Check (Abschnitt 0)

Regeln 1 (Nährwerte pro 100g), 2 (Rundung), 10 (keine Primitives), 11 (Discriminated Unions), 14
(`decimal(8,2)`) betreffen noch keine konkreten Felder in M0 — werden aber hier als
Value-Object-/Tagged-Union-**Basismuster** einmal exemplarisch dokumentiert (Vorlage-Beispiel im
`shared_kernel`, kein fachliches Value Object selbst), damit jeder folgende Meilenstein dasselbe
Muster übernimmt statt es neu zu erfinden.

## Tests (Abschnitt 9)

- Unit-Tests für `Result[T, E]`, `TimeProvider`-Fake, Idempotenz-Decorator (Key zweimal ⇒ zweite
  Antwort `200` statt `201` — hier schon als Mechanismus-Test, bevor ein echter Endpunkt existiert).
- Architekturtest: `import-linter`-Lauf ist Teil der Testsuite (schlägt fehl, sobald ein Context
  eine fremde Domain/Infrastructure importiert).
- Smoke-Test: `docker compose up` + `curl` gegen einen Health-Endpunkt (`GET /api/v1/health` o.ä.)
  liefert `200`.
