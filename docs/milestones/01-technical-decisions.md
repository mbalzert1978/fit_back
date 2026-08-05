# Technische Entscheidungen dieser Portierung

Der Draft (`docs/Draft/BACKEND.md`) beansprucht fachliche Vollständigkeit für ASP.NET Core/C#.
Für die Python-Portierung mussten zusätzlich rein technische Entscheidungen getroffen werden, die
der Draft naturgemäß nicht trifft. Diese wurden mit dem Auftraggeber abgestimmt (Antworten unten
übernommen) und gelten ab sofort als verbindlicher Rahmen für alle Meilensteine/Tickets.

## Stack

| Baustein | Entscheidung |
|---|---|
| Sprache | Python **3.14**, `uv` als Paketmanager |
| Lint/Format | `ruff` (inkl. `ANN`-Regelsatz), **kein** mypy/pyright — siehe `.rules/python/README.md` |
| Web-Framework | **FastAPI** (Routing, OpenAPI, Pydantic-Request-Validierung an der äußeren Naht) |
| Persistenz | **PostgreSQL**, **SQLAlchemy 2.0 (async)**, Treiber **asyncpg** |
| Migrationen | **Alembic**, ein Migrations-Strang je `DbSchema` (`identity`, `catalog`, `diary`, `recipes`, `goals`, `health`, `shared`) |
| Hintergrund-Verarbeitung (OCR-Agent) | **Postgres-natives Job-Queue-Pattern**, kein Redis/Broker: Tabelle `catalog.ocr_jobs` mit `SELECT … FOR UPDATE SKIP LOCKED` für nebenläufige Worker plus `LISTEN/NOTIFY` für sofortige Zustellung statt Polling-Latenz. Worker läuft als eigener Prozess/Task im selben Deployment. |
| Blob-Speicher (`BlobReference`, Nährwertfotos) | **S3-kompatibel von Anfang an**: MinIO lokal (Docker Compose), AWS S3 (oder kompatibel) in Produktion. Angebunden über einen `BlobStorage`-Port (`Protocol`) in `infrastructure/adapters/`. |
| Bounded-Context-Grenzen | **`import-linter`** mit Contract-Datei (`.importlinter`) erzwingt: kein Context importiert aus einem anderen Context außer über dessen `application`-Schicht (Application-Services) bzw. über Domain Events; kein Context greift auf ORM-Modelle eines anderen Contexts zu. Läuft als eigener CI-/Lint-Schritt neben `ruff`. |
| Lokale Infrastruktur & manuelles Testen | **Docker Compose von Beginn an** (Postgres, MinIO, App-Container) — siehe M0. Manuelles/exploratives Testen gegen die laufenden Container erfolgt mit **`curl`** (Auftraggeber-Vorgabe), zusätzlich zu den automatisierten Tests aus Abschnitt 9 des Drafts (pytest, Testcontainers). `curl`-Beispielaufrufe je Endpunkt gehören in die Tickets/README, nicht nur in automatisierte Tests. |
| Auth | JWT (Access/Refresh) — konkrete Bibliothek (`pyjwt` o.ä.) und Passwort-Hashing (Argon2id via `argon2-cffi`) werden im M1-Ticket zur Auth-Pipeline final gewählt; Argon2id ist durch den Draft (Abschnitt 1, `PasswordHash`) bereits vorgegeben, nicht offen. |

## Repo-/Code-Layout

Kombiniert die Context-Ebene aus dem Draft (Abschnitt 0: „ein Projekt pro Bounded Context, je
eine Schicht Domain/Application/Infrastructure") mit der Feature-Slice-Form aus
`.rules/python/python-feature-slices.md` (Use-Case-Ebene innerhalb von `application/`):

```
src/
  contexts/
    identity/
      domain/            # Aggregate, VOs, Domain-Ports (Protocol), Domain-Regeln — nur stdlib
      application/
        register_user/   # ein Ordner je Use Case: request.py, response.py, command.py,
        login/           # handler.py, request_mapper.py, response_mapper.py, validators/
        ...
        ports/           # von mehreren Use Cases geteilte public Ports (Gateways)
      infrastructure/
        persistence/     # SQLAlchemy-Modelle, Repository-Adapter, ValueConverters
        adapters/         # externe Adapter (JWT, Argon2, ...)
      tests/
        register_user/   # Tests nur über die public Test-API des Use Cases
    catalog/
    diary/
    recipes/
    goals/
    health_sync/
  api/
    identity/            # FastAPI-Router je Context — übersetzt HTTP ⇄ Application-DTOs
    catalog/
    ...
  shared_kernel/         # Result[T,E]-Basis, TimeProvider-Protocol, ProblemDetails/RFC7807,
                         # Idempotency-Middleware, IUserOwned-Mixin, UUIDv7-Helper, DbSchema-Basis
alembic/
  identity/ catalog/ ... # ein versions/-Strang je Context-Schema
docker/
  docker-compose.yml     # postgres, minio, app
  Dockerfile
.importlinter
pyproject.toml
```

`domain/` hängt ausschließlich an der stdlib (siehe `python-feature-slices.md`); Aggregate werden
context-weit unter `domain/` geteilt (mehrere Use Cases derselben Aggregatwurzel), nicht je Use
Case dupliziert — das entspricht sowohl dem Draft („ein Aggregate pro Context") als auch der
Regel, dass eine Aggregatwurzel ihre Operationen selbst besitzt.

## Cross-Context-Kommunikation (Entkopplung für spätere Microservice-Extraktion)

Rahmenbedingung: Start als modularer Monolith, aber maximale Entkopplung der Module, damit
einzelne Contexts bei Bedarf später als eigene Services herausgeschnitten werden können. Der
Draft erlaubt in Abschnitt 0 zwei Kanäle ("Application-Services oder Domain Events, In-Process,
MediatR") — diese Entscheidung legt fest, **wann welcher Kanal gilt** und wie beide so gebaut
werden, dass eine spätere Extraktion nur den Adapter austauscht, nie die Fachlogik:

1. **Fire-and-forget-Reaktionen ohne Rückgabewert für den Publisher** (`UserRegistered` →
   Goals-Default/Diary-Standard-Slots; `UserDeletionRequested`/`UserDeleted` → alle Contexts)
   laufen über **asynchrone Integration Events via Postgres-Outbox**: Event wird transaktional mit
   dem Aggregate-Write in `shared.outbox` geschrieben, Zustellung über dasselbe
   `SELECT … FOR UPDATE SKIP LOCKED` + `LISTEN/NOTIFY`-Muster wie der OCR-Job (M5) — kein
   synchrones In-Process-`Publish`, das Publisher und Handler in derselben Transaktion verankert.
   Der Outbox-Eintrag ist bereits die Nachricht, die bei einer Extraktion unverändert auf einen
   echten Broker (SNS/Kafka/RabbitMQ) umgestellt wird.
2. **Interaktionen mit sofortigem Rückgabewert für den Aufrufer** (`Recipes.PortionsToDiary` →
   `Diary.AddEntry`; `Diary.GetDay` → HealthSync-`activities`; jede Sync-Batch-Operation → ihr
   Ziel-Context) laufen synchron, aber ausschließlich über ein **vom aufrufenden Context selbst
   definiertes, schmales `Protocol`-Port** (Anti-Corruption Layer — der Aufrufer besitzt die
   Schnittstelle, nicht der Zielcontext). Die heutige Implementierung ruft in-process den
   Application-Service des Zielcontexts auf, **niemals** dessen Domain/Handler/ORM-Modelle direkt.
   Bei einer Extraktion wird nur der Adapter (In-Process-Call → HTTP/gRPC-Client) ausgetauscht.

Begründung: Die eigentliche Kopplungsgefahr liegt nicht in "Event vs. Service-Call", sondern
darin, wessen Schnittstelle bei einem synchronen Aufruf gilt — ein direkter Import des
Zielcontexts koppelt Prozess- und Codegrenze, ein aufrufer-eigenes Port entkoppelt beide. Der
Outbox-Mechanismus erspart einen Broker im Monolithen-Stadium (konsistent mit der
Postgres-statt-Redis-Entscheidung für M5), verhält sich aber am Tag der Extraktion bereits wie
eine echte Messagequeue. Shared-Kernel-Baustein: `shared.outbox`-Tabelle + Relay-Worker gehören zu
M0 (siehe `m0-projekt-grundgeruest.md`).

## Offene Feinentscheidungen, die erst im jeweiligen Ticket getroffen werden

Diese sind bewusst nicht hier vorweggenommen, weil sie use-case-lokal sind und keine
Architekturentscheidung mit repo-weiter Tragweite darstellen:

- Konkrete JWT-Bibliothek (M1).
- Konkretes OCR-Vision-Modell hinter `INutritionOcrAgent`/`OcrAgent`-Port (M5) — der Draft fordert
  explizit nur den Port, die Implementierung ist austauschbar.
- Konkrete Struktur der `.importlinter`-Contracts je Context-Paar (M0-Ticket, aber Detailarbeit).
