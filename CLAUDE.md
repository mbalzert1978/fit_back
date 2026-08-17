# CLAUDE.md

**Diese Datei behauptet nichts über das Repo. Sie verlinkt nur.** Jede Aussage darüber, wie der
Code aufgebaut ist, was wo liegt oder was gilt, steht genau einmal — dort, wohin hier verwiesen
wird. Was hier inline steht, sind Regeln für den Agenten; sie können nicht gegen den Code driften.
Wächst diese Datei um einen Absatz, der etwas über das Repo behauptet, gehört er woandershin.

## Wo die Dinge liegen

- [`docs/architecture.md`](docs/architecture.md) — vor jeder Annahme über Aufbau, Schichten,
  Contexts oder Querschnitts-Regeln zuerst hierher, und nirgends sonst nachschlagen.
- [`CONTEXT.md`](CONTEXT.md) — das Glossar. Bevor ein Begriff neu geprägt oder ein Synonym benutzt
  wird, zuerst hierher; ein Begriff, der dort geschärft wurde, wird auch im Code so genannt.
- [`docs/Draft/BACKEND.md`](docs/Draft/BACKEND.md) — die fachliche Spezifikation.
- [`docs/milestones/01-technical-decisions.md`](docs/milestones/01-technical-decisions.md) — der
  Tie-Breaker, wann immer Spezifikation und Stack sich scheinbar widersprechen.
- [`docs/milestones/`](docs/milestones/) — Meilenstein-Zerlegung, Einstieg
  [`00-overview.md`](docs/milestones/00-overview.md).
- Die Tickets des Backend-Baus liegen als GitHub-Issues unter der Map
  [#40](https://github.com/mbalzert1978/fit_back/issues/40); wie man sie abfragt, anlegt und
  schließt, steht in [`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md). Implementiert
  wird aus dem passenden Issue heraus, nie direkt aus dem Draft.
- [`docs/decisions/`](docs/decisions/) — je eine Datei pro Entscheidung, siehe unten.
- [`docs/reflections/`](docs/reflections/) — destillierte Lektionen früherer Sitzungen. Vor einer
  neuen Welle die `README.md` dort lesen.
- [`docs/reference/`](docs/reference/) — Lesenotizen zu fremden Quellen. Eine Notiz dort ändert an
  `.rules/` **nichts**, solange kein Decision-Doc sie annimmt.
- [`docs/agents/`](docs/agents/) — Konventionen, auf die die Skills sich stützen (u. a. der
  Issue-Tracker).
- [`docs/claude/README.md`](docs/claude/README.md) — was in `.claude/` liegt und wer es liest;
  Einstieg für die Claude-Seite des Repos, inklusive `./make.ps1 claude-doctor`.
- [`.rules/`](.rules/) — die verbindlichen Coding-Standards. Einstieg und Konfliktauflösung:
  [`.rules/python/README.md`](.rules/python/README.md).

## Befehle

`./make.ps1` im Repo-Root ist der kanonische Task-Runner; `./make.ps1 help` listet die Targets.
Ihn benutzen statt Ad-hoc-Kommandos.

Für Planung, Review, Lint- und Test-Workflows die Skill-Bibliothek unter `.claude/skills/`
bevorzugen — ihr Index steht in [`.claude/skills/CLAUDE.md`](.claude/skills/CLAUDE.md).

## Entscheidungen und Memory-Policy

**Kein externer, sitzungsübergreifender Memory-Mechanismus** — weder Claude Codes Memory-System
noch irgendeine Notiz-Ablage außerhalb des Repos. Das gilt für das Anlegen neuer Einträge wie für
das Belassen bestehender; es sollten keine existieren.

Entscheidungen und relevante Neuerungen werden **ausschließlich** als Datei unter
[`docs/decisions/`](docs/decisions/) erfasst (Format und Benennung: `README.md` dort), destillierte
Lektionen unter [`docs/reflections/`](docs/reflections/). Verbindlich für jede künftige Sitzung in
diesem Repository.

## Sprache der Dokumentation

**Alle Dokumentation und jede projektbezogene Notiz werden auf Deutsch verfasst** — neu erstellte
Dateien ebenso wie Überarbeitungen bestehender; abweichend englischsprachige Dateien werden bei
Gelegenheit der Bearbeitung nachgezogen. Ausgenommen sind repo-übergreifend wiederverwendete
Infrastruktur, die nicht zum fachlichen Inhalt dieses Projekts gehört (z. B.
`.claude/skills/`-Definitionen und deren `config.json`), sowie Code, Bezeichner und Kommentare
selbst. Verbindlich für jede künftige Sitzung in diesem Repository.
