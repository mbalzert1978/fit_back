# Hook-Portfolio: neun Hooks gehen, der jq-Nudge bleibt

**Datum:** 2026-08-13, 07:22
**Status:** entschieden
**Herkunft:** [Wayfinder-Ticket #18](https://github.com/mbalzert1978/fit_back/issues/18), Kind der
[Wayfinder-Map #25](https://github.com/mbalzert1978/fit_back/issues/25)
**Vorgänger:** [Wann ein Hook seine Existenz verdient](2026-08-13-0641-hook-kriterium-und-abschied-von-den-dotnet-hooks.md)
— dessen Kriterium wird hier unverändert angewandt.

## Der Anlass

In `.claude/hooks/` lagen zehn Skripte, die in keiner Settings-Datei registriert waren: toter
Code, der wie aktive Absicherung aussieht. Die Frage war, welche verdrahtet und welche gelöscht
werden.

## Der tragende Befund: die Shell ist meist gar nicht der beste Weg

Acht der zehn Dateien sind `prefer-*`-Hooks. Sie erzwingen moderne Kommandozeilen-Werkzeuge —
`bat` statt `cat`, `fd` statt `find`, `rg` statt `grep`. Der erste Einwand gegen das Löschen war
berechtigt: diese Werkzeuge **sind** besser als ihre Vorgänger, und sie sind lokal vorhanden.

Der Einwand zeigt aber woanders hin. Bei sechs der acht ist der beste Weg für einen Agenten nicht
die Shell, sondern das eigene Tool des Harness — und das schlägt **beide** Shell-Varianten:

| Hook | Wird geschlagen von | Warum |
|---|---|---|
| `prefer-rg-over-grep` | `Grep` | Das Tool **ist** ripgrep, integriert in Permissions und Datei-Links. |
| `prefer-fd-over-find` | `Glob` | Deckt Dateisuche vollständig ab. |
| `prefer-bat-over-cat` | `Read` | Liest Dateien ohne ANSI-Rahmen. |
| `prefer-bat-over-read` | `Read` | Schießt direkt gegen das Tool, das der Harness bevorzugt. |
| `prefer-sd-over-sed` | `Edit` | Dateiänderung gehört ins Edit-Tool, nicht in einen Stream-Editor. |
| `prefer-delta-over-diff` | — | `delta` ist ein Pager für Augen. Für ein Kontextfenster ist ANSI-Farbe Rauschen. |

Diese sechs Hooks treiben den Agenten also von der besseren Route **weg**, in die Shell hinein.
Bei `bat`, `delta` und `eza` kommt hinzu, dass sie Farbe und Rahmen-Chrom in den Kontext
schreiben.

`prefer-eza-over-ls` fällt als Grenzfall: der Gewinn gegenüber `ls` ist für einen Agenten Chrom,
kein Signal.

Zwei weitere Gründe treffen die ganze Klasse: **kein** Werkzeug aus dieser Liste kommt in
`.rules/` vor — es gibt also gar keine Regel dieses Repos, die sie durchsetzen würden. Und fünf
der acht blockieren hart (`exit 2`); ein Fehlalarm blockiert damit ein gültiges Kommando, während
der verhinderte „Verstoß" rein kosmetisch ist. Das reißt Bedingung 2 des Kriteriums.

## Was bleibt: `prefer-jq-over-grep-json`

Ein Hook überlebt. Für JSON gibt es **kein** Tool im Harness, die Shell ist hier tatsächlich der
Weg, und strukturiertes Abfragen schlägt Zeilen-Matching. Er wird umgebaut:

- **Von Blocker zu Nudge**: `exit 0` mit `additionalContext` statt `exit 2` mit `stderr`. Ein
  Fehlalarm kostet dann Text, nicht ein blockiertes Kommando.
- **Verdrahtet** als `PreToolUse` mit Matcher `Bash` in `settings.json`.
- **Python mit `uv run`** bleibt — siehe „Verworfen: die PowerShell-Umstellung" unten.

## Der vierte .NET-Hook, den #15 übersehen hat

`prefer-declarative-loops.py` ist **verdrahtet** und war deshalb nicht Teil der ursprünglichen
Frage. Das Doc zu #15 führt ihn als „sprachneutral" und lässt ihn stehen. **Das ist falsch:**

- Er importiert `cs_file_path` und ruft es auf. Die Funktion steigt bei jedem Pfad aus, der nicht
  auf `.cs` endet. `git ls-files "*.cs"` ist leer — der Hook kann nicht feuern.
- Sein Text handelt von LINQ und `foreach` und verweist auf `.rules/csharp/csharp-control-flow.md`.
  Dieses Verzeichnis existiert nicht.
- **#15 löscht `cs_file_path()`.** Damit bricht dieser Hook bei jedem `Edit`/`Write` mit einem
  ImportError.

Er wird ebenfalls gelöscht, und zwar zusammen mit der Umsetzung von #15 — sonst hinterlässt #15
einen kaputten Hook. Danach hat `settings.json` keinen `PreToolUse(Edit|Write)`-Eintrag mehr.

## Die geteilten Module

Das Doc zu #15 sagt, `_hook_utils.py` und `_utils.py` hätten „je 14 Benutzer". Für
`_hook_utils.py` stimmt das. **`_utils.py` hat genau einen Benutzer:** `_hook_session_state.py` —
und den löscht #15 bereits.

- `_utils.py` (11 KB) wird damit zur Waise und **wird gelöscht**.
- `_hook_utils.py` **bleibt**, eingedampft auf `load_hook_input`. Es behält zwei Abnehmer: den
  jq-Nudge und `session-state-handler.py`.

## Verworfen: die PowerShell-Umstellung

Zwischenzeitlich stand im Raum, die verbleibenden Hooks nach PowerShell zu portieren — passend zu
`make.ps1` und ohne `uv` als Abhängigkeit. Gemessen wurde dafür der Prozessstart, je drei Läufe:

| Start | Zeit |
|---|---|
| `powershell -NoProfile` | 776 / 862 / 1053 ms |
| `uv run python` | 852 / 870 / 907 ms |

Die Umstellung hätte also nichts gespart. Dazu ist `pwsh` (7.x) hier nicht installiert; Ziel wäre
Windows PowerShell 5.1 mit dessen scharfen Kanten gewesen. **Entschieden: Python und `uv`
bleiben.**

Die Messung hat aber den Preis offengelegt, der ohnehin bestand: **rund 0,9 s Prozessstart pro
Bash-Aufruf** für den jq-Nudge. Der Handel — dieser Preis, damit zwei Zeilen nicht in `CLAUDE.md`
stehen — wurde bewusst angenommen, weil `CLAUDE.md` minimal bleiben soll (siehe unten).

## Ergebnis

| Datei | Verdikt |
|---|---|
| `prefer-bat-over-cat` · `-bat-over-read` · `-rg-over-grep` · `-fd-over-find` · `-sd-over-sed` · `-delta-over-diff` · `-eza-over-ls` | gelöscht |
| `prefer-jq-over-grep-json` | bleibt, als Nudge, verdrahtet |
| `smart-approve.py` | gelöscht |
| `suggest-compact.py` | gelöscht |
| `prefer-declarative-loops.py` | gelöscht (4. .NET-Hook) |
| `_utils.py` | gelöscht |
| `_hook_utils.py` | bleibt, auf `load_hook_input` eingedampft |
| `session-state-handler.py` | bleibt |

Danach enthält `.claude/hooks/` drei `.py`-Dateien: zwei verdrahtet, eine mit `_`-Präfix. Das ist
das Abnahmekriterium von #18.

### `smart-approve.py` im Einzelnen

Dieser Hook gibt Bash-Kommandos automatisch frei. Er ist der einzige des Portfolios, der eine
Prüfung **ausschaltet** statt etwas zu erzwingen — damit dreht sich Bedingung 2 des Kriteriums um:
ein Fehlalarm ist hier eine Falsch-**Freigabe**, also genau der teure Fall. Dazu kommen 20 KB
Fremdcode (MIT, `liberzon/claude-hooks`), der Shell-Dekomposition nachbaut — Subshells, Heredocs,
Redirections, Env-Zuweisungen. Jeder Parser-Bug darin ist eine Freigabe, die niemand erteilt hat.
Und sein Verhalten hängt an der **globalen** `~/.claude/settings.json`, also an Zustand außerhalb
des Repos.

Der Schmerz dahinter ist echt, hat aber ein sanktioniertes Mittel:
[#16 Permissions bereinigen](https://github.com/mbalzert1978/fit_back/issues/16) und
`/fewer-permission-prompts`.

### `suggest-compact.py` im Einzelnen

`.claude/skills/strategic-compact` existiert bereits und hat dieselbe Aufgabe — zwei Quellen
derselben Wahrheit, genau das Muster, das das Kriterium ausschließt. Inhaltlich zählt der Hook
Tool-Aufrufe in einer Temp-Datei; ein Zähler ist kein Kontext-Maß. Preislich war er der teuerste
des Portfolios: ein Prozessstart bei **jedem** Tool-Aufruf, nur um eine Zahl zu erhöhen.

## Folgen

- Die **Umsetzung** läuft über die normale Ticket-Pipeline, nicht über die Map. Sie muss mit der
  Umsetzung von #15 koordiniert werden, weil `prefer-declarative-loops.py` an dem `cs_file_path()`
  hängt, das dort gelöscht wird.
- Der Fog-Eintrag der Map *„Ist `smart-approve.py` sicherheitlich vertretbar?"* ist damit
  **erledigt** statt vertagt und wird gestrichen.
- Der Fog-Eintrag *„Hook-Latenz beim Session-Start"* schrumpft: von zehn unverdrahteten plus vier
  registrierten Hooks bleiben drei Dateien. Die Messung oben liefert die Zahl schon mit — ~0,9 s
  je Prozessstart.
- **Die Destination der Map war unvollständig.** Das eigentliche Hauptziel dieser
  Strukturierungsarbeit ist eine minimale, überwiegend verlinkende `CLAUDE.md`; die Hook-Fragen
  waren nur der erste Weg dorthin. Die Destination wird entsprechend umgeschrieben, und das Kürzen
  bekommt ein eigenes Grilling-Ticket.
- [#23 Grenzen-Abschnitt in CLAUDE.md](https://github.com/mbalzert1978/fit_back/issues/23) will
  einen Abschnitt **hinzufügen** und steht damit gegen das neue Hauptziel. Es wird im neuen
  Kürzungs-Ticket erneut beurteilt.

---

## Nachtrag 2026-08-13, aus der Umsetzung von #26

Zwei Aussagen dieses Docs sind bei der Ausführung nicht aufgegangen:

1. **`_hook_utils.py` ist nicht „auf `load_hook_input` eingedampft"**, sondern auf **zwei**
   Funktionen: `load_hook_input` *und* `bash_command`. Zweiteres braucht der jq-Nudge, der genau
   dieses Doc am Leben hält — die Aussage widersprach also der eigenen Entscheidung eine Tabelle
   weiter oben. Gefallen sind nur die C#-Teile (`cs_file_path`, `cs_new_fragments`,
   `evaluate_csharp_rule_signals` samt Regexen und Kommentarblock) und das damit unbenutzte
   `import re`.
2. **Es sind vier `.py`-Dateien, nicht drei.** Das Abnahmekriterium stammt von #18 und ist vor #20
   geschrieben worden, das den Worktree-Wächter hinzufügte. Endstand: `_hook_utils.py`,
   `forbid-write-outside-worktree.py`, `prefer-jq-over-grep-json.py`, `session-state-handler.py`.

Dazu ein gemessener Befund, der die Reichweite von `./make.ps1 ci` betrifft: **`.claude/` ist über
`exclude` in `[tool.ruff]` für `ruff check` *und* `ruff format --check` unsichtbar.** Nachgewiesen
mit einer absichtlich fehlformatierten Sonde in `.claude/hooks/`: `ruff format --check .` meldete
„313 files already formatted" und übersah sie, derselbe Aufruf mit explizitem Pfad meldete sie.
Anders als bei den `per-file-ignores` aus #29 greift `exclude` also für beide Kommandos. Für jede
Hook-Änderung heißt das: **`ci` ist kein Beleg** — die Hooks müssen einzeln mit einer echten
Nutzlast gefahren werden.
