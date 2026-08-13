# Wann ein Hook seine Existenz verdient — und warum die drei .NET-Hooks ersatzlos gehen

**Datum:** 2026-08-13, 06:41
**Status:** entschieden
**Herkunft:** [Wayfinder-Ticket #15](https://github.com/mbalzert1978/fit_back/issues/15), Kind der
[Wayfinder-Map #25](https://github.com/mbalzert1978/fit_back/issues/25)

## Der Anlass

In [`.claude/settings.json`](../../.claude/settings.json) waren vier `PreToolUse`-Hooks
registriert, drei davon Altlasten aus der C#/.NET-Vorlage dieses Repos. Die Frage war, ob sie
je nach Python portiert oder ersatzlos gelöscht werden — und, dahinter, nach welchem Maßstab
das übrige Hook-Portfolio überhaupt beurteilt wird.

## Die Entscheidung, die alle anderen trägt: das Kriterium

> **Ein Hook ist nur gerechtfertigt, wenn er etwas erzwingt, das `./make.ps1 ci` und die Gates
> strukturell nicht können — weil es eine Anweisung an den Agenten *vor* dem Schreiben ist, nicht
> eine Prüfung des Ergebnisses.**
>
> Dazu zwei Bedingungen:
> 1. Der Hook muss auf ein Signal zeigen, das im Repo **heute existiert**.
> 2. Ein Fehlalarm muss **billiger** sein als der Verstoß, den der Hook verhindert.

Verworfen wurden zwei Alternativen:

| Verworfen | Warum |
|---|---|
| „Ein Hook ist gerechtfertigt, wenn er schneller meldet als die CI, auch bei Überschneidung." | Macht jede CI-Regel doppelt implementierbar. Zwei Quellen derselben Wahrheit driften auseinander — genau das ist unten bei `csharp-rules-reminder.py` passiert. |
| „Ein Hook ist gerechtfertigt, wenn er irgendeinen Verstoß verhindert, Redundanz egal." | Kein Kriterium, sondern dessen Abwesenheit. Damit ist jeder Hook begründbar. |

Das Kriterium ist die operative Fassung der Ponytail-Linie „Löschen schlägt Portieren" aus den
Notes der Map: prüfbar statt Geschmackssache.

## Die drei Altlasten: alle drei gelöscht, keine portiert

Der Befund war in allen drei Fällen härter als die Ausgangslage des Tickets vermutet hatte —
es ging nicht um „lohnt sich das Portieren", sondern um wirkungslosen Code.

### `csharp-rules-reminder.py`

`_hook_utils.cs_file_path()` steigt bei jedem Pfad aus, der nicht auf `.cs` endet.
`git ls-files "*.cs"` ist leer. **Der Hook konnte nicht feuern.** Er verwies zudem auf zwei
Dinge, die es nicht gibt: das Verzeichnis `.rules/csharp/` und eine „C#-Regel-Trigger-Tabelle"
in `CLAUDE.md`.

Dieser letzte Punkt ist der lehrreiche. `_hook_utils.py` trug den Kommentar *„Single source of
truth: CLAUDE.md, section C#-Regel-Trigger-Tabelle. Keep this function and that table in sync."*
Die Tabelle ist irgendwann verschwunden, der Hook lief weiter und zeigte ins Leere. **Niemand hat
es bemerkt, weil nichts es prüfte.**

### `forbid-guid-newguid.py`

Dieselbe `.cs`-Schranke, dieselbe Folge: konnte nicht feuern.

### `forbid-dotnet-test.py`

Dieser Hook lief tatsächlich — er sucht `\bdotnet\s+test\b` in *jedem* Bash-Kommando.
`git grep dotnet` außerhalb von `.claude/` ist leer. **Null echte Treffer möglich, nur
Fehlalarme.** Er scheitert damit an beiden Zusatzbedingungen zugleich.

### Warum „stört ja nicht" nicht stimmt

Zwei Kosten, die das Liegenlassen gehabt hätte: je ein `uv run`-Prozessstart pro `Edit`/`Write`
für Hooks, die nichts tun können — und, schwerer, ein `settings.json`, das sich für jede spätere
Sitzung wie gültige Politik des Repos liest.

## Kein Python-Nachfolger — für keinen der drei

### Regel-Reminder auf `.rules/python/`: nein

Das ist der knappste Fall, denn das Kriterium spricht zunächst *dafür*: Die CI kann dem Agenten
nichts *vor* dem Schreiben sagen. Diese Lücke ist echt.

Er scheitert an Bedingung 1. Der Hook zeigte nicht auf ein vorhandenes Signal, sondern auf eine
Trigger-Tabelle, die für Python erst zu erfinden wäre — 13 Regel-Dateien, von Hand gepflegt, von
nichts geprüft. Die C#-Fassung ist der Beweis, dass diese Bauart nicht hält (siehe oben).

Hinzu kommt, dass die Lücke schmaler ist als sie aussieht: `CLAUDE.md` nennt
`.rules/python/README.md` bereits als Einstieg, und `/review-against-rules` prüft die Regeln beim
Review. Der Hook läge zwischen zwei Dingen, die es schon gibt.

### `uuid4()`-Verbot: kein Hook — aber ruff

Hier greift das Kriterium unmittelbar: **ruff kann das prüfen**, also darf es kein Hook sein.
Ein Eintrag unter `[tool.ruff.lint.flake8-tidy-imports.banned-api]` verbietet `uuid.uuid4`.

Die Sorge vor Fehlalarmen, die zunächst gegen den ruff-Eintrag sprach, hat sich nicht bestätigt:
`uuid4()` steht heute ausschließlich in `tests/middleware/test_idempotency_api.py`, und
`"tests/**" = ["ALL"]` steht bereits in den `per-file-ignores`. Der Eintrag hätte **null
Fehlalarme**.

Die inhaltliche Regel steht in `.rules/python/python-modern-syntax.md`, Abschnitt
„Sortierbare IDs: `uuid.uuid7()` statt `uuid.uuid4()`".

### `pytest`-Verbot: nein

Beim .NET-Vorbild gab es einen Grund: genau ein funktionierender Testaufruf, gekapselt im Skill.
Bei Python fehlt dieser Unterschied. `./make.ps1 test` ruft `uv run pytest`, und die
`config.json` des `/run-tests`-Skills ruft `uv run pytest`. Ein direkter Aufruf ist kein Fehler —
**es gibt nichts zu schützen**, und ein solcher Hook würde das eigene Werkzeug des Repos
blockieren.

## Die verwaiste Maschinerie geht mit

Mit `csharp-rules-reminder.py` verlieren weitere Teile ihren einzigen Abnehmer. Auch sie werden
gelöscht:

| Teil | Warum weg |
|---|---|
| `.claude/hooks/track-rules-read.py` | Schrieb ausschließlich den Zustand, den der C#-Hook las. Dazu der `PostToolUse(Read)`-Eintrag in `settings.json`. |
| `.claude/hooks/_hook_session_state.py` | Nur zwei Benutzer: der C#-Hook und `track-rules-read.py`. Beide gehen. |
| `evaluate_csharp_rule_signals()`, `cs_file_path()`, `cs_new_fragments()` samt Regexen in `_hook_utils.py` | Die C#-spezifischen Teile des Moduls. |

**Nicht** gelöscht werden `_hook_utils.py` und `_utils.py` selbst — sie haben je 14 Benutzer,
darunter `session-state-handler.py` und sämtliche `prefer-*`-Hooks.

## Folgen

- Von den vier registrierten `Edit|Write`-Hooks bleibt `prefer-declarative-loops.py`; er ist
  sprachneutral und war nie Teil dieser Frage.
- Die **Umsetzung** (Dateien löschen, `settings.json` bereinigen, ruff-Eintrag setzen) läuft über
  die normale Ticket-Pipeline, nicht über die Wayfinder-Map — so steht es in deren Destination.
- [Ticket #18](https://github.com/mbalzert1978/fit_back/issues/18) („Welche der zehn
  unverdrahteten Hooks bleiben?") war durch #15 blockiert und ist jetzt frei. Es erbt das
  Kriterium oben unverändert; das war der ausdrückliche Zweck dieser Reihenfolge.
- Der zuvor als „vielleicht" geführte ruff-Eintrag gegen `uuid.uuid4` ist damit entschieden und
  gehört in dasselbe Umsetzungs-Ticket.
