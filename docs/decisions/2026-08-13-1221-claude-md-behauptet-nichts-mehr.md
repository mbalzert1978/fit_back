# `CLAUDE.md` behauptet nichts mehr über das Repo — Architektur zieht nach `docs/architecture.md`

**Datum:** 2026-08-13, 12:21
**Ticket:** [#27 — Was bleibt in CLAUDE.md, was wird zum Link?](https://github.com/mbalzert1978/fit_back/issues/27)
**Map:** [#25 — Hook-Portfolio und semble-Anbindung des Claude-Setups](https://github.com/mbalzert1978/fit_back/issues/25)

## Die Frage, die das Ticket stellte — und die falsche Prämisse darin

Das Ticket wollte `CLAUDE.md` von 118 auf unter 100 Zeilen kürzen und begründete das damit, der
Architektur-Block (Zeilen 44–94) „dupliziere" `docs/milestones/01-technical-decisions.md` und
`docs/milestones/02-test-pyramide.md`.

**Die Duplikations-Prämisse hält nicht.** Gemessen am Ist-Zustand des Repos widersprechen sich die
beiden Bäume, und der in `CLAUDE.md` ist der richtige:

| Sache | `CLAUDE.md` | `01-technical-decisions.md` | Ist-Zustand |
|---|---|---|---|
| Testverzeichnis | `specs/` | `tests/` | `src/contexts/identity/specs/` — `CLAUDE.md` |
| Contracts-Schicht | `contracts/` | fehlt ganz | `src/contexts/identity/contracts/` — `CLAUDE.md` |
| Shared Kernel | `contexts/shared_kernel/` | `src/shared_kernel/` | `src/contexts/shared_kernel/` — `CLAUDE.md` |
| Import-Linter-Config | `setup.cfg` | `.importlinter` | `setup.cfg`; `.importlinter` existiert nicht |
| `middleware/`, `settings.py`, `main.py` | genannt | fehlen | existieren alle |

Wer das Ticket wörtlich umgesetzt hätte — Block streichen, Link setzen —, hätte die einzige
korrekte Layout-Beschreibung des Repos gelöscht und dafür auf eine veraltete gezeigt.

`02-test-pyramide.md` ist im Gegensatz dazu eine echte, reichere Quelle; der Verweis dorthin in
`CLAUDE.md` war immer schon ein Verweis und keine Dopplung.

## Der zweite Fund: `CLAUDE.md` ist ihrerseits verrottet

Zeile 92 fordert „ausschließlich `DateTimeOffset`-Zeitstempel". Das ist seit dem 2026-08-06 durch
[`2026-08-06-1340-unix-epoch-statt-datetime.md`](2026-08-06-1340-unix-epoch-statt-datetime.md)
überschrieben — ein Zeitpunkt ist in Domäne und Persistenz ein `int` Unix-Sekunden. Der Code folgt
der Entscheidung (`src/contexts/shared_kernel/timestamp.py`), `CLAUDE.md` folgt ihr seit einer
Woche nicht.

Damit beschreiben **drei** Stellen die Architektur, alle drei uneinig, keine kanonisch. Das ist kein
Längenproblem. Es ist bereits eingetretene Drift.

## Entscheidung

### Der Schnitt: Behauptung gegen Regel

`CLAUDE.md` wird in **jede** Sitzung geladen; `docs/` und `.rules/` werden **auf Anfrage** gelesen.
Daraus folgt die Trennung, an der die Kürzung entlangläuft:

- **Behauptungen über das Repo** (wie der Code aufgebaut ist, was wo liegt, welche Querschnitts-
  Regeln gelten) — sie können veralten, also gehören sie an genau eine Stelle und werden von
  `CLAUDE.md` nur **verlinkt**.
- **Regeln für den Agenten** (was er tun muss, was er nie darf) — sie sind keine Aussagen über den
  Code und können deshalb nicht gegen ihn driften. Sie bleiben **inline**, weil ein Riegel hinter
  einem Link unverbindlich ist.

**Die Leitlinie: `CLAUDE.md` behauptet nichts über das Repo.** Sie ist ein kurzer Einstieg für den
Agenten aus Regeln, Tooling und Links — so knapp wie möglich. Drift zwischen `CLAUDE.md` und den
Dokumenten wird damit strukturell unmöglich, weil `CLAUDE.md` nichts mehr behauptet, das driften
könnte.

### Kein Zeilenziel

Die „unter 100 Zeilen" des Tickets entfallen als Abnahmekriterium. Die Zahl ist bereits einmal als
Verhandlungsmasse benutzt worden — [#23](https://github.com/mbalzert1978/fit_back/issues/23)
argumentiert sie weg, statt die Frage zu beantworten. Das Kriterium ist stattdessen: **jede Aussage
steht genau einmal im Repo, `CLAUDE.md` wiederholt keine davon.** Die Zeilenzahl fällt als
Nebenprodukt.

### Eine Datei hält die Architektur — nicht mehrere

Neu: **`docs/architecture.md`** als lebende Referenz. Sie bekommt aus `CLAUDE.md` den
Verzeichnisbaum, die Context-Liste, die Cross-Context-Kommunikationsregeln und den
Querschnitts-Regeln-Absatz — Letzteren beim Umzug gegen den Ist-Zustand geprüft, damit die
`DateTimeOffset`-Zeile nicht mitwandert.

`01-technical-decisions.md` **verliert** seine Abschnitte „Repo-/Code-Layout" und
„Cross-Context-Kommunikation" und verlinkt stattdessen dorthin. Zwei Architektur-Beschreibungen
nebeneinander wären wieder zwei Dinge, die gegeneinander driften können — es ist genau eine.

Warum nicht einfach das Milestone-Dokument reparieren: Es heißt „Technische **Entscheidungen**" und
trägt eine Sektion „Nachträgliche Entscheidungen, die diese Datei ergänzen". Es ist der Bauart nach
ein **Protokoll**, an das man anhängt, statt die Vergangenheit zu korrigieren. Genau deshalb ist
sein Baum verwahrlost. Protokoll und lebende Referenz sind zwei Genres; sie in einer Datei zu halten
hat die Drift erst erzeugt. Das Protokoll behält Stack-Tabelle und Entscheidungshistorie.

### Was in `CLAUDE.md` bleibt

1. Links auf `docs/` und `.rules/` (die heutige Sektion „Wo die Dinge liegen", auf Zeilen statt
   Absätze eingedampft)
2. Tooling: `./make.ps1`, die Skill-Bibliothek unter `.claude/skills/`
3. Regel: Entscheidungen nach `docs/decisions/`, kein externer Memory
4. Regel: Dokumentation auf Deutsch
5. Später: der Grenzen-Abschnitt aus #23

Punkt 3 und 4 sind Verhaltensregeln, keine Behauptungen — sie bleiben zu Recht inline.

### Gegen das Zuwachsen: ein Satz, kein Hook

In `CLAUDE.md` selbst steht künftig sinngemäß: *„Diese Datei behauptet nichts über das Repo. Sie
verlinkt nur."*

**Kein Hook.** Das Hook-Kriterium dieser Map verlangt ein Signal, das `./make.ps1 ci` strukturell
nicht sehen kann — „ist dieser Absatz eine Behauptung oder eine Regel?" kann eine Maschine nicht
entscheiden. Ein Hook darauf gäbe nur Fehlalarm, und Fehlalarm ist hier teurer als der Verstoß.

### `CONTEXT.md` wird angelegt

Im **Repo-Root**, weil sowohl `docs-code-consistency` als auch `verify-issue-breakdown` sie dort
erwarten und das die Konvention des `domain-modeling`-Skills ist. Alles andere hieße wieder etwas
hart zu verdrahten.

**Klein angefangen:** nur die Begriffe, über die schon gestritten wurde — nicht alle Fachbegriffe
aller sechs Contexts auf Vorrat. Sie wächst, wenn ein Ticket einen Begriff schärft. Ein Glossar auf
Vorrat beschreibt Begriffe, die noch niemand gebraucht hat.

Architektur und Glossar bleiben **getrennte** Dateien: `docs/architecture.md` ist Struktur,
`CONTEXT.md` ist Vokabular.

### Die zwei Skills werden umgehängt

`docs-code-consistency` und `verify-issue-breakdown` suchen `CONTEXT.md` **und** `docs/adr/`.
Ersteres entsteht hiermit; Letzteres gibt es hier nicht und wird es nicht geben — diese Rolle spielt
`docs/decisions/`. Beide Pfade werden in einem Griff richtiggestellt, nicht nur der eine.

### #23 bleibt offen

Der Grenzen-Abschnitt überlebt als Punkt 5 der Liste oben — unter dem Schnitt dieser Entscheidung
ist er der reinste Riegel, den die Datei haben kann, und damit das Gegenteil eines Link-Kandidaten.
Seine Ausgestaltung wird an #23 selbst entschieden. Der Teil „mindestens fünf belegte Punkte" sollte
dabei fallen: eine Mindestanzahl lädt zum Auffüllen ein.

## Ausführung

Vier `wayfinder:task`-Kinder der Map, nicht die normale Ticket-Pipeline — der Satz des Tickets
„Das Kürzen selbst ist Ausführung und läuft über die normale Ticket-Pipeline" ist älter als die
heutige Destination der Map und damit überholt.

1. `docs/architecture.md` anlegen; `01-technical-decisions.md` verliert seine zwei Abschnitte.
2. `CLAUDE.md` kürzen (hängt an 1, sonst zeigt der Link ins Leere).
3. `CONTEXT.md` anlegen, klein.
4. Die zwei Skills umhängen (hängt an 3).

1 und 3 sind voneinander frei und können parallel laufen.

## Regel für diese Map

**Eine Behauptung, die an zwei Stellen steht, ist bereits eine Drift mit Verzögerung.** Diese Runde
fand drei Beschreibungen derselben Architektur, die in fünf Punkten auseinanderliefen — ohne dass je
etwas fehlgeschlagen wäre. Wo diese Map künftig Inhalt verschiebt statt löscht, gehört die Frage
dazu, **welche einzelne Stelle danach die Wahrheit hält** und ob die übrigen sie wirklich verloren
haben.

Die sechste Stufe derselben Familie: #22 prüft die **Ausgangslage**, #20 die **mitgelieferte
Lösung**, #30 den **Ausfallmodus**, #29 den **Geltungsbereich** eines Kommandos, #21 den
**Geltungsbereich einer eigenen früheren Notiz** — und hier die **Anzahl der Stellen**, an denen
eine Aussage steht.

## Nachtrag vom 2026-08-13 aus der Ausführung ([#32](https://github.com/mbalzert1978/fit_back/issues/32))

Beim Anlegen von `docs/architecture.md` haben zwei Aussagen dieser Entscheidung nicht gehalten:

**Es waren vier Stellen, nicht drei.** Gezählt wurden `CLAUDE.md`, `01-technical-decisions.md` und
`02-test-pyramide.md`. Übersehen wurde `README.md`, Abschnitt „Project Structure" — ein vierter
Baum, und der falscheste von allen: er zeigt `src/shared_kernel/` auf oberster Ebene (dort liegt
der Shared Kernel seit dem 2026-08-06 nicht mehr) und kennt `middleware/`, `infrastructure/`,
`settings.py` und `main.py` überhaupt nicht. Er ist mit umgezogen. Die Regel dieser Entscheidung
hat sich damit an ihrer eigenen Ausführung bewährt und zugleich geschärft: **die Anzahl der Stellen
wird gesucht, nicht geschätzt** — hier per `grep` über alle `.md` des Repos.

**Der Querschnitts-Absatz war an zwei weiteren Punkten falsch, nicht nur an der
`DateTimeOffset`-Zeile.** Die Anweisung „beim Umzug gegen den Ist-Zustand geprüft" war richtig, ihr
Anlass zu eng gefasst:

- Das RFC-7807-Format ist **nicht** im Shared Kernel, sondern seit dem Neuschnitt vom 2026-08-06 in
  `src/api/` — es ist HTTP-Rand, kein Domänen-Vokabular.
- `RowVersion`/`If-Match` existiert im Repo **überhaupt nicht**; der Baustein wurde am 2026-08-06
  entfernt und kommt als Fall des `DomainError` seines Context wieder, nicht als
  Shared-Kernel-Typ.

Der Satz „einmalig in `shared_kernel` implementiert statt je Context" stimmte damit für zwei von
acht Punkten und war für zwei nachweislich falsch. In `docs/architecture.md` steht der Absatz
deshalb als Tabelle mit einer Spalte „Stand in diesem Repo" — die Form macht es teurer, einen Punkt
unbelegt mitzuschleppen.

`m0-projekt-grundgeruest.md` und zwei Issue-Dateien verweisen in Prosa auf die beiden umgezogenen
Abschnittstitel. Sie sind **nicht** angefasst worden; stattdessen behält
`01-technical-decisions.md` an ihrer Stelle einen Abschnitt, der beide alten Titel nennt und
weiterleitet. Ein Meilenstein-Plan ist Protokoll wie diese Datei — er wird nicht nachträglich
umgeschrieben, damit ein Link kürzer wird.
