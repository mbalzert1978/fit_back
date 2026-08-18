# Architektur

**Diese Datei ist die einzige lebende Architektur-Referenz des Repos.** Wer wissen will, wie der
Code aufgebaut ist, was wo liegt und welche Querschnitts-Regeln gelten, liest hier — und nirgends
sonst. `CLAUDE.md`, `README.md` und
[`docs/milestones/01-technical-decisions.md`](milestones/01-technical-decisions.md) verlinken
hierher, statt es zu wiederholen.

Diese Datei beschreibt den **Ist-Zustand** und wird korrigiert, sobald er sich ändert — anders als
`docs/decisions/` und `01-technical-decisions.md`, die als **Protokolle** anhängen, statt die
Vergangenheit zu korrigieren. Warum die Trennung nötig wurde:
[`2026-08-13-1221`](decisions/2026-08-13-1221-claude-md-behauptet-nichts-mehr.md).

Stand der Messung: 2026-08-13. Gebaut ist bisher der Slice `identity/register_user`; die übrigen
fünf Contexts existieren als leere Schichten-Gerüste.

## Modularer Monolith, ein Bounded Context je Modul

```
src/
  contexts/
    <context>/
      domain/                    # Aggregate, Entitäten, Value Objects, Domain-Ports (Protocol)
        entities/                # — nur stdlib
        ports/
        value_objects/
      application/
        <use_case>/              # ein Ordner je Use Case
          command.py             # Eingabe des Handlers
          handler.py             # der Use Case selbst
          pipeline.py            # Verdrahtung der Schritte
          request.py             # Außengrenze rein
          response.py            # Außengrenze raus, als Union aller Ausgänge
          abstractions/          # Ports, die dieser Use Case selbst definiert
          adapters/              # deren Umsetzung auf Domäne bzw. Infrastruktur
          mappers/               # einer je Richtung
          validators/            # Regeln des Use Case
          fakes/                 # Doubles für die Test-API
          test_api/              # öffentliche Test-API des Use Case
      infrastructure/            # SQLAlchemy-Modelle/Repositories, externe Adapter
      contracts/                 # veröffentlichtes Vokabular für andere Contexts — nur Primitive
      specs/<use_case>/          # Tests ausschließlich über die Test-API des Use Case
    shared_kernel/               # Result[T,E], Timestamp, TimeProvider, EventPublisher/-Registry,
                                 # CodedError, NotEmptyString, IUserOwned, Rule-Pattern,
                                 # pipeline.py (Handler/Behavior/build_pipeline)
                                 # — hängt an nichts außer der stdlib
      behaviors/                 # je ein konkretes Querschnitts-Behavior der Pipeline
                                 # (heute validating.py; künftig Transaktionsklammer,
                                 # Idempotenz, Messung) — die Naht selbst kennt keines
  api/                           # FastAPI-Router, ProblemDetails, Exception-Handler, i18n,
    <context>/                   # Composition Root - je Context ein Unterordner
    resources/                   # i18n-Ressourcen (de-DE.json, en-US.json)
  middleware/                    # ASGI-Middleware: Idempotency-Key, Auffangpunkt für
                                 # unbehandelte Ausnahmen
  infrastructure/                # kontextübergreifende Infrastruktur: Outbox + Relay, DB-Schemata
  settings.py                    # Konfiguration aus der Umgebung, geprüft beim Start
  main.py                        # nur Zusammenbau: Middleware, Handler, Router, Lifespan

tests/                           # Integrationstests über Schichtgrenzen (API, Persistenz, Outbox)
alembic/<schema>/                # ein versions/-Strang je DB-Schema
setup.cfg                        # import-linter-Contracts
pyproject.toml                   # Projekt, Abhängigkeiten, ruff
docker-compose.yml / Dockerfile  # lokale Infrastruktur: postgres, minio, app
make.ps1                         # kanonischer Task-Runner
```

**Kein weiteres Top-Level-Paket neben `api/`, `middleware/`, `infrastructure/`, `contexts/`.** Was
neu entsteht, gehört in eines davon oder braucht eine eigene Entscheidung
([`2026-08-06-1620`](decisions/2026-08-06-1620-repo-layout-und-aufgeraeumter-einstiegspunkt.md)).

Die Form eines Slice — welche Datei welche Aufgabe hat, warum die Test-API ein ausgeliefertes
Artefakt ist, warum die Naht dem Use Case gehört — steht in
[`.rules/python/python-feature-slices.md`](../.rules/python/python-feature-slices.md) und wird hier
bewusst nicht wiederholt.

### Abhängigkeitsrichtung, maschinell abgesichert

Die Reihenfolge im Baum ist die Abhängigkeitsrichtung: `src/main.py` kennt alles, der Shared Kernel
niemanden. Das ist keine Vereinbarung, sondern in `setup.cfg` als `import-linter`-Contract geprüft
und läuft als eigener Schritt in `./make.ps1 ci`:

| Contract | Was er erzwingt |
|---|---|
| `domain-purity` | Domänen-Schichten, `contracts/` und der Shared Kernel hängen nur an der stdlib — verboten sind FastAPI, Starlette, Pydantic, SQLAlchemy, asyncpg, Alembic **und** `src.api`, `src.middleware`, `src.infrastructure`, `src.main`, `src.settings` |
| `context-layers` | je Context strikt einseitig nach innen: `infrastructure` → `application` → `domain` → `contracts` |
| `forbidden` | kein Context importiert `domain` oder `infrastructure` eines anderen Contexts |

`contracts/` liegt zuinnerst: es ist das veröffentlichte Vokabular, das andere Contexts importieren
dürfen. Würde es die eigene Domäne kennen, zöge jeder Konsument diese über den Vertrag mit herein.
Die Schicht ist optional — sie greift automatisch, sobald ein Context sie anlegt.

Der Shared Kernel liegt unter `src/contexts/`, weil er das geteilte **Modell** der Contexts ist und
kein Rahmenwerk daneben. Etwas gehört nur dann hinein, wenn es ohne jede externe Abhängigkeit
auskommt **und** einen zweiten Nutzer hat
([`2026-08-06-1330`](decisions/2026-08-06-1330-shared-kernel-neuschnitt.md)); erfüllt es nur die
erste Hälfte, bleibt es, wo es entstanden ist.

## Contexts

`identity`, `catalog`, `diary`, `recipes`, `goals`, `health_sync` — je ein PostgreSQL-Schema, kein
Context greift je auf die Tabellen eines anderen zu. Dazu das Schema `shared` für
kontextübergreifende Infrastruktur (Outbox, Idempotency-Keys); `health_sync` liegt auf dem Schema
`health`. Alembic führt je Schema einen eigenen `versions/`-Strang.

## Cross-Context-Kommunikation

Bewusst eingeschränkt, mit einem Ziel: Contexts sollen sich später als eigene Services herauslösen
lassen, ohne ihre Logik umschreiben zu müssen. Die eigentliche Kopplungsgefahr liegt nicht in
„Event vs. Service-Call", sondern darin, **wessen Schnittstelle bei einem synchronen Aufruf gilt**.

1. **Fire-and-forget-Reaktionen ohne Rückgabewert für den Publisher** (`UserRegistered` →
   Goals-Default-Profil, Diarys Standard-Mahlzeiten-Slots; `UserDeletionRequested`/`UserDeleted` →
   alle Contexts) laufen über eine **Postgres-gestützte Outbox**: das Event wird transaktional mit
   dem Aggregate-Write nach `shared.outbox` geschrieben, die Zustellung läuft über
   `SELECT … FOR UPDATE SKIP LOCKED` + `LISTEN/NOTIFY` — nie über direktes In-Process-Dispatching,
   das Publisher und Handler in dieselbe Transaktion zwingt. Der Outbox-Eintrag ist bereits die
   Nachricht, die bei einer Extraktion unverändert auf einen echten Broker geht.
2. **Interaktionen mit sofortigem Rückgabewert für den Aufrufer** (`Recipes.PortionsToDiary` →
   `Diary.AddEntry`; `Diary.GetDay` → HealthSync-`activities`) laufen synchron, aber ausschließlich
   über ein **vom aufrufenden Context selbst definiertes, schmales `Protocol`-Port** — der Aufrufer
   besitzt die Schnittstelle, nicht der Zielcontext (Anti-Corruption Layer). Die Implementierung
   ruft in-process den Application-Service des Zielcontexts auf, **niemals** dessen
   Domain-/Handler-/ORM-Code direkt. Bei einer Extraktion wird nur der Adapter getauscht
   (In-Process-Call → HTTP/gRPC-Client).

Für genau diese beiden Grenzarten hat die Test-Pyramide eine eigene **Contract-Tests-Ebene**,
zwischen Domain-Unit-Tests und Integrationstests — siehe
[`docs/milestones/02-test-pyramide.md`](milestones/02-test-pyramide.md), bevor Tests geschrieben
werden, die eine Context-Grenze überschreiten.

## Querschnitts-Regeln

Regeln, die für jeden Context gelten. Ihre fachliche Quelle ist `docs/Draft/BACKEND.md`,
Abschnitt 0 — **aber der Draft ist für ASP.NET Core/C# geschrieben, und drei der Punkte sind für
diesen Python-Port inzwischen überschrieben oder anders verortet.** Maßgeblich ist die rechte
Spalte:

| Regel | Stand in diesem Repo |
|---|---|
| Nährwerte immer pro 100 g | gilt wie spezifiziert; noch kein Code (Catalog ist ungebaut) |
| Rundung ist reine Präsentationssache | gilt wie spezifiziert; noch kein Code |
| RFC-7807-Fehlerformat | gebaut, aber **nicht im Shared Kernel**: `src/api/problem_details.py` und `src/api/exception_handlers.py` — das Format ist HTTP-Rand, kein Domänen-Vokabular ([`2026-08-06-1330`](decisions/2026-08-06-1330-shared-kernel-neuschnitt.md)) |
| JWT-Auth (Access/Refresh) | noch nicht gebaut; Bibliothekswahl steht im M1-Ticket zur Auth-Pipeline |
| Keine Primitive Obsession | gilt; die Domäne spricht nur VOs/Entitäten, siehe [`python-feature-slices.md`](../.rules/python/python-feature-slices.md) |
| Tagged Unions statt Enums | gilt und ist gebaut (`identity/domain/value_objects/account_status.py`); jedes `match` darüber endet mit `assert_never` ([`2026-08-07-1120`](decisions/2026-08-07-1120-jeder-match-endet-mit-assert-never.md)) |
| ~~ausschließlich `DateTimeOffset`-Zeitstempel~~ | **überschrieben:** ein Zeitpunkt ist in Domäne und Persistenz ein `int` Unix-Sekunden im Value Object `Timestamp`; der Transport bleibt ISO-8601 ([`2026-08-06-1340`](decisions/2026-08-06-1340-unix-epoch-statt-datetime.md)) |
| Optimistische Nebenläufigkeit über `RowVersion`/`If-Match` | **existiert heute nicht.** Der Shared-Kernel-Baustein wurde am 2026-08-06 entfernt, weil er Kontrollfluss über Exceptions war; ein Versionskonflikt ist ein Fall des `DomainError` seines Context. Entsteht neu mit dem ersten echten Update-Pfad — [`0024`](issues/0024-m3-updateproduct-owner-only-if-match.md) und [`0037`](issues/0037-m6-updaterecipe-zutaten-crud-deleterecipe.md); [`0011`](issues/0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md) nimmt es ausdrücklich aus seinem Schnitt ([`2026-08-06-1330`](decisions/2026-08-06-1330-shared-kernel-neuschnitt.md)) |

Die frühere Zusammenfassung „einmalig in `shared_kernel` implementiert statt je Context" hielt
nicht: sie stimmt für `Result[T,E]` und `Timestamp`, für das Fehlerformat ist der Ort seit dem
Neuschnitt `src/api/`, und für `RowVersion` gibt es gar keinen Ort mehr.

Ein fachlicher Fehlausgang ist nie eine Exception, sondern ein typisierter Fall der Response-Union
des Slice; der Router wählt daraus Statuscode und Body. Was die Middleware für unbehandelte
Ausnahmen erreicht, ist per Definition kein Fachfall
([`2026-08-06-1620`](decisions/2026-08-06-1620-repo-layout-und-aufgeraeumter-einstiegspunkt.md),
[`2026-08-07-0646`](decisions/2026-08-07-0646-fehlernutzlast-als-typisierter-fall-ist-regel.md)).
