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
| Blob-Speicher (`BlobReference`, Nährwertfotos) | **S3-kompatibel von Anfang an**: lokal der aktiv gepflegte Fork **`pgsty/minio`** (Docker Compose) — das ursprüngliche `minio/minio` ist seit Dezember 2025 im „Maintenance Mode" und wurde am 25.04.2026 als GitHub-Repo archiviert, siehe [`2026-08-05-0956-minio-fork-statt-archiviertem-minio-minio.md`](../decisions/2026-08-05-0956-minio-fork-statt-archiviertem-minio-minio.md) —, AWS S3 (oder kompatibel) in Produktion. Angebunden über einen `BlobStorage`-Port (`Protocol`) in `infrastructure/adapters/`. |
| Bounded-Context-Grenzen | **`import-linter`** mit Contract-Datei (`.importlinter`) erzwingt: kein Context importiert aus einem anderen Context außer über dessen `application`-Schicht (Application-Services) bzw. über Domain Events; kein Context greift auf ORM-Modelle eines anderen Contexts zu. Läuft als eigener CI-/Lint-Schritt neben `ruff`. |
| Lokale Infrastruktur & manuelles Testen | **Docker Compose von Beginn an** (Postgres, MinIO, App-Container) — siehe M0. Manuelles/exploratives Testen gegen die laufenden Container erfolgt mit **`curl`** (Auftraggeber-Vorgabe), zusätzlich zu den automatisierten Tests aus Abschnitt 9 des Drafts (pytest, Testcontainers). `curl`-Beispielaufrufe je Endpunkt gehören in die Tickets/README, nicht nur in automatisierte Tests. |
| Auth | JWT (Access/Refresh) über `pyjwt`, hinter der Naht `RegisterUserSessionTokens`; Passwort-Hashing Argon2id via `argon2-cffi`. Gewählt in [#95](https://github.com/mbalzert1978/fit_back/issues/95), siehe [2026-08-21-2230](../decisions/2026-08-21-2230-pyjwt-hinter-der-naht-refresh-token-als-hash.md). |

## Repo-/Code-Layout und Cross-Context-Kommunikation

**Beide Abschnitte sind am 2026-08-13 nach
[`docs/architecture.md`](../architecture.md) umgezogen** — dort stehen der Verzeichnisbaum, die
Context-Liste, die maschinell geprüfte Abhängigkeitsrichtung, die beiden erlaubten Kanäle zwischen
Contexts (Postgres-Outbox für Fire-and-forget, aufrufer-eigenes `Protocol`-Port für synchrone
Aufrufe) und die Querschnitts-Regeln.

Der Grund im Volltext:
[`2026-08-13-1221`](../decisions/2026-08-13-1221-claude-md-behauptet-nichts-mehr.md).

Was hier bleibt, ist das Protokoll: die Stack-Tabelle oben und die Entscheidungshistorie unten.

## Nachträgliche Entscheidungen, die diese Datei ergänzen

Getroffen nach dem ersten gebauten Slice und dort begründet — sie gelten repo-weit und schlagen,
wo angegeben, die Draft-Spezifikation:

- [`2026-08-06-0751`](../decisions/2026-08-06-0751-slice-form-test-api-baureihenfolge.md) —
  Slice-Form, Test-API als ausgeliefertes Artefakt, gestufte Baureihenfolge.
- [`2026-08-06-1105`](../decisions/2026-08-06-1105-shared-kernel-validation-und-tzdata.md) —
  Rule Pattern im `shared_kernel`, `tzdata` als Laufzeit-Dependency.
- [`2026-08-06-1340`](../decisions/2026-08-06-1340-unix-epoch-statt-datetime.md) — Zeitpunkte sind
  Unix-Sekunden in einem Value Object. **Überschreibt BACKEND.md §0.12** (`DateTimeOffset`/
  `timestamptz`) für diesen Python-Port; der Transport bleibt ISO-8601.

## Offene Feinentscheidungen, die erst im jeweiligen Ticket getroffen werden

Diese sind bewusst nicht hier vorweggenommen, weil sie use-case-lokal sind und keine
Architekturentscheidung mit repo-weiter Tragweite darstellen:

- Konkretes OCR-Vision-Modell hinter `INutritionOcrAgent`/`OcrAgent`-Port (M5) — der Draft fordert
  explizit nur den Port, die Implementierung ist austauschbar.
- Konkrete Struktur der `.importlinter`-Contracts je Context-Paar (M0-Ticket, aber Detailarbeit).
