# CLAUDE.md

Diese Datei gibt Claude Code (claude.ai/code) Orientierung für die Arbeit in diesem Repository.

## Wo die Dinge liegen

- [`docs/Draft/BACKEND.md`](docs/Draft/BACKEND.md) — die vollständige fachliche Spezifikation,
  ursprünglich für ASP.NET Core/C# geschrieben. Dieses Repo ist **Python 3.14**, daher wird die
  Spezifikation portiert, nicht wörtlich umgesetzt. Vor jeder Annahme zu einer Technologie-Wahl
  erst [`docs/milestones/01-technical-decisions.md`](docs/milestones/01-technical-decisions.md)
  lesen — dort steht jede Entscheidung, die zur Anpassung der Spezifikation an diesen Stack
  getroffen wurde (Web-Framework, Persistenz, Hintergrund-Jobs, Blob-Storage,
  Cross-Context-Kommunikation, Repo-Layout), und sie ist der Tie-Breaker, wann immer sich
  Spezifikation und Stack scheinbar widersprechen.
- [`docs/milestones/`](docs/milestones/) — die aus der Spezifikation abgeleitete
  Meilenstein-Zerlegung (M0–M8).
- [`docs/issues/`](docs/issues/) — Tracer-Bullet-Issues, die die Meilensteine umsetzen, vor
  Veröffentlichung durch den Skill `verify-issue-breakdown` gegengeprüft. Implementiert wird aus
  dem passenden Issue heraus, nicht direkt aus `docs/Draft/BACKEND.md` — das Issue hat die
  Spezifikation bereits gegen Stack und Layout dieses Repos aufgelöst. Der Fortschritt eines
  Issues lebt in dessen eigenem Frontmatter (`issue-status`-Skill), nicht in einem zentralen
  Changelog.
- [`.rules/`](.rules/) — Coding-Standards (`common/` sprachunabhängig, `python/`
  Python-spezifisch). Zuerst `.rules/python/README.md` lesen — dort stehen Leseweg und
  Auflösung von Konflikten zwischen den Dateien.
- [`docs/decisions/`](docs/decisions/) — siehe „Entscheidungen und Memory-Policy" unten.

## Befehle

`make.ps1` im Repo-Root ist der kanonische Task-Runner (PowerShell, kein GNU-Make nötig) — sie ist
in Git getrackt, sodass dieselben `./make.ps1 <target>`-Befehle im Haupt-Checkout und in jedem
Worktree unter `.claude/worktrees/` identisch funktionieren. `./make.ps1 help` listet die Targets;
`./make.ps1 ci` führt lint + format-check + import-lint + test aus.

Für Planung, Review, Lint- und Test-Workflows die Skill-Bibliothek unter `.claude/skills/`
bevorzugen (z. B. `to-issues`, `verify-issue-breakdown`, `review-against-rules`, `qa-check`,
`lint-and-format-check`, `run-tests`) statt Ad-hoc-Befehlen — mehrere `config.json`-Dateien dort
sind bereits auf den Python/uv/ruff/pytest-Stack dieses Repos eingerichtet.

## Architektur

**Modularer Monolith, ein Bounded Context je Modul**, gemäß
[`docs/milestones/01-technical-decisions.md`](docs/milestones/01-technical-decisions.md):

```
src/contexts/<context>/domain/            # Aggregate, Value Objects, Domain-Ports (Protocol) — nur stdlib
src/contexts/<context>/application/<use_case>/   # ein Ordner je Use Case: Command, Handler, Mapper, Validatoren
src/contexts/<context>/infrastructure/    # SQLAlchemy-Modelle/Repositories, externe Adapter
src/contexts/<context>/specs/<use_case>/  # Tests ausschließlich über die öffentliche Test-API des Use Case
src/api/<context>/                        # FastAPI-Router — nur HTTP <-> Application-DTOs
src/shared_kernel/                        # Result[T,E], TimeProvider, RFC-7807-ProblemDetails,
                                           # Idempotency-Key-Middleware, IUserOwned, UUIDv7, Outbox
```

Contexts: `identity`, `catalog`, `diary`, `recipes`, `goals`, `health_sync` — je ein
PostgreSQL-Schema, kein Context greift je auf die Tabellen eines anderen zu.

**Cross-Context-Kommunikation ist bewusst eingeschränkt** (Ziel: Contexts sollen sich später als
eigene Services herauslösen lassen, ohne ihre Logik umschreiben zu müssen):
- Fire-and-forget-Reaktionen (z. B. `UserRegistered`, das ein Default-Goals-Profil oder Diarys
  Standard-Mahlzeiten-Slots auslöst) laufen über eine **Postgres-gestützte Outbox**
  (`SELECT ... FOR UPDATE SKIP LOCKED` + `LISTEN/NOTIFY`), nie über direktes In-Process-Event-
  Dispatching.
- Synchrone Aufrufe, bei denen der Aufrufer ein unmittelbares Ergebnis braucht (z. B. Recipes, das
  Diary aufruft), laufen über einen **vom Konsumenten definierten `Protocol`-Port** — der
  aufrufende Context definiert die schmale Schnittstelle, die er braucht, und die
  Port-Implementierung ruft den Application-Service des Ziel-Contexts in-process auf, nie dessen
  Domain-/Handler-/ORM-Code direkt.

Die **Test-Pyramide** hat für genau diese beiden Grenzarten eine explizite
Contract-Tests-Ebene, zwischen Domain-Unit-Tests und Integrationstests angesiedelt — siehe
[`docs/milestones/02-test-pyramide.md`](docs/milestones/02-test-pyramide.md), bevor Tests
geschrieben werden, die eine Context-Grenze überschreiten.

Querschnitts-Regeln, die für jeden Context gelten (Nährwerte immer pro 100 g, Rundung ist reine
Präsentationssache, RFC-7807-Fehlerformat, JWT-Auth, keine Primitive Obsession, Tagged Unions
statt Enums, ausschließlich `DateTimeOffset`-Zeitstempel, optimistische Nebenläufigkeit über
`RowVersion`/`If-Match`) sind in `docs/Draft/BACKEND.md`, Abschnitt 0, spezifiziert und einmalig
in `shared_kernel` implementiert statt je Context.

## Entscheidungen und Memory-Policy

**Für dieses Repository wird kein externer/persistenter Memory-Mechanismus genutzt** — weder
Claude Codes sitzungsübergreifendes Memory-System noch irgendeine andere Notiz-Ablage außerhalb
des Repos. Das gilt sowohl für das Anlegen neuer Einträge als auch für das Belassen bestehender;
es sollten keine existieren.

Entscheidungen und relevante Neuerungen werden **ausschließlich** unter
[`docs/decisions/`](docs/decisions/) erfasst, eine Datei je Entscheidung, benannt
`YYYY-MM-DD-HHMM-<slug>.md`, datiert und mit Uhrzeit versehen zum Moment der tatsächlichen
Entscheidung. Das ist verbindlich für alle künftigen Sitzungen in diesem Repository.

## Sprache der Dokumentation

**Alle Dokumentation und Informationen zu diesem Repository werden auf Deutsch verfasst** —
`docs/` (Milestones, Issues, Decisions, Draft-Spezifikation), diese `CLAUDE.md` sowie jede
weitere projektbezogene Notiz. Das gilt für neu erstellte Dateien ebenso wie für Überarbeitungen
bestehender; abweichend englischsprachige Dateien werden bei Gelegenheit der Bearbeitung
nachgezogen. Ausgenommen sind generische, repo-übergreifend wiederverwendete Infrastruktur, die
nicht zum fachlichen Inhalt dieses Projekts gehört (z. B. `.claude/skills/`-Definitionen und deren
`config.json`), sowie Code, Bezeichner und Kommentare selbst, die den üblichen Sprachkonventionen
für Quellcode folgen. Diese Vorgabe ist verbindlich für alle künftigen Sitzungen in diesem
Repository.
