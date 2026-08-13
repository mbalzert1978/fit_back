# Worktree-Wächter: Standort statt Projektverzeichnis-Vergleich

**Datum:** 2026-08-13, 09:59
**Ticket:** [#20 Worktree-Guard als PreToolUse-Hook](https://github.com/mbalzert1978/fit_back/issues/20)
(`wayfinder:task` der Map [#25](https://github.com/mbalzert1978/fit_back/issues/25))
**Status:** entschieden und umgesetzt

## Ausgangslage

Ticket #20 verlangte einen `PreToolUse`-Hook, der „Pfade außerhalb des `CLAUDE_PROJECT_DIR`
der laufenden Session mit Exit-Code 2 ablehnt". Anlass war der Vorfall vom 2026-08-07
([Incident-Doc](2026-08-07-1416-incident-subagent-schreibt-im-haupt-checkout.md)): ein
Sub-Agent des Entwickler-Agenten schrieb 34 Dateien im Haupt-Checkout statt im Worktree.

## Befund: die spezifizierte Regel war wirkungslos

Die Prämissen des Tickets hielten dem Ist-Zustand nicht stand:

| Prämisse | Ist-Zustand |
|---|---|
| Der Hook lehnt Pfade *außerhalb* von `CLAUDE_PROJECT_DIR` ab | Worktrees liegen unter `.claude/worktrees/` — **innerhalb** des Haupt-Checkouts |
| Der Worktree-Agent hat ein eigenes Projektverzeichnis | Claude Code startet **einmal** im Haupt-Checkout; Agenten gelangen per `cd` in den Worktree |
| Der Sub-Agent schrieb „außerhalb" | Er schrieb nach `<Haupt-Checkout>/src` und `/alembic` — **innerhalb** von `CLAUDE_PROJECT_DIR` |

Jeder beteiligte Pfad liegt unter `CLAUDE_PROJECT_DIR`. Der spezifizierte Hook hätte am
2026-08-07 **nichts** abgelehnt — er wäre ein No-Op gegen seinen eigenen Anlassfall gewesen.

## Gemessen, nicht geglaubt

Der Hook-Vertrag wurde gegen die offizielle Dokumentation und anschließend **live** geprüft:

- **`cwd` folgt dem `cd`.** Das Nutzlast-Feld ist „current working directory when the hook is
  invoked". Live bestätigt: nach `cd` in den Worktree meldete die Nutzlast den Worktree, nicht
  den Startort. Damit ist der Standort des Aufrufers überhaupt erst prüfbar.
- **Hooks feuern in Sub-Agenten.** „When a subagent calls a tool, tool events such as
  `PreToolUse` … fire the same configured hooks as in the main conversation."
- **`agent_id` markiert den Sub-Agenten.** „Present only when the hook fires inside a subagent
  call." Das ist der Diskriminator — **nicht** `agent_type`, denn das ist laut Dokumentation auch
  bei Sitzungen gesetzt, die mit `--agent` starten, und würde einen so gestarteten Teamlead
  fälschlich fangen.
- **Hooks werden mitten in der Sitzung neu geladen.** Die Änderung an `.claude/settings.json`
  wirkte ohne Neustart — belegt durch die scharfe Ablehnung im Test unten.
- **`worktree-erstellen` liefert einen in sich geschlossenen Worktree.** `.claude/skills`,
  `agents`, `hooks` und `settings.json` kommen „provided by checkout"; es werden keine Junctions
  gelegt. Die Sorge, ein Schreibzugriff könne über eine Junction in den Haupt-Checkout
  durchschlagen, ist damit gegenstandslos.

## Entscheidung

Der Wächter prüft **den Standort des Aufrufers**, nicht den Abstand zum Projektverzeichnis.
`.claude/hooks/forbid-write-outside-worktree.py`, registriert auf `Edit|Write|NotebookEdit`:

| Fall | `cwd` | Bedingung | Verhalten |
|---|---|---|---|
| 1 | im Worktree | — | Jeder Schreibzugriff in den Haupt-Checkout wird abgelehnt |
| 2 | im Haupt-Checkout | `agent_id` gesetzt **und** ≥1 Worktree registriert | Jeder Schreibzugriff in den Haupt-Checkout wird abgelehnt |
| 3 | im Haupt-Checkout | sonst | Der Wächter tut nichts |

Pfade **außerhalb** des Repos (Scratchpad, Temp) sind in allen Fällen frei — ein Wächter, der
Zwischendateien blockiert, produziert Fehlalarme in normaler Arbeit und wird abgeschaltet.

Fall 2 ist die eigentliche Lehre aus dem Vorfall: der schuldige Sub-Agent war für einen Hook von
einer legitimen Haupt-Checkout-Sitzung **nicht unterscheidbar** — gleiches Verzeichnis, gleiche
Pfade, gleiche Werkzeuge. `agent_id` ist das einzige Merkmal, das ihn verrät. Ohne Fall 2 schützt
der Wächter nur den Agenten, der sich ohnehin richtig verhält.

Fall 2 sperrt den **ganzen** Repo-Root, nicht bloß die Code-Bäume, weil `fit-back-teamlead` nie
als Sub-Agent läuft und seine legitimen Schreibzugriffe nach `docs/` damit unter Fall 3 fallen.

Gegen das Hook-Kriterium aus [#15](https://github.com/mbalzert1978/fit_back/issues/15) gehalten:
`./make.ps1 ci` sieht strukturell nicht, *wohin* geschrieben wird (a); `cwd`, `agent_id` und
`git worktree list` sind heute existierende Signale (b); ein Fehlalarm kostet eine Handbewegung,
der Verstoß kostete 34 Dateien und eine Rettungsaktion (c).

## Nachweis

Sieben Fälle synthetisch, zwei davon zusätzlich scharf in der laufenden Sitzung:

- **Scharf abgelehnt** (Fall 1): `cd` in `.claude/worktrees/wachter-test`, dann `Write` auf
  `docs/_wachter_probe.txt` → Exit 2 mit Angabe von Arbeitsverzeichnis und Ziel.
- **Scharf durchgelassen**: derselbe Schreibzugriff aus dem Haupt-Chectout heraus bei offenem
  Worktree (Fall 3); Schreibzugriff in den eigenen Worktree; Schreibzugriff ins Scratchpad.

**Fall 2 ist am echten Sub-Agenten gemessen**, nicht aus der Dokumentation übernommen. Ein
Sub-Agent mit Arbeitsverzeichnis im Haupt-Checkout — also exakt die Konstellation vom
2026-08-07 — versuchte bei offenem Worktree einen `Write` nach `docs/`:

```
Blockiert: Sub-Agent schreibt in den Haupt-Checkout, waehrend ein Worktree offen ist.
  Ziel: C:\temp\apps\fit_back\docs\_fall2_probe.txt
```

Damit ist belegt, dass Claude Code 2.1.229 `agent_id` tatsächlich in die Nutzlast legt. Die
Gegenprobe lief ebenfalls: derselbe Sub-Agent, derselbe Zielpfad, **kein** Worktree registriert →
Schreibzugriff geht durch. Der Wächter bleibt im Normalbetrieb still.

## Abgrenzungen

- **`Bash` wird nicht abgedeckt.** Über `>`, `sd` oder `git checkout` lässt sich ebenfalls
  schreiben. Das mitzufangen hieße, Kommandozeilen zu parsen — genau die Bauart, die
  [#18](https://github.com/mbalzert1978/fit_back/issues/18) bei den sechs `prefer-*`-Hooks als
  unzuverlässig verworfen hat. Bekannte Lücke, bewusst offen.
- **Der Wächter fällt offen aus.** Lässt sich der Haupt-Checkout weder über `git` noch über
  `CLAUDE_PROJECT_DIR` bestimmen, lehnt er nichts ab. Fail-closed wäre unbenutzbar, aber das ist
  ein Ausfall mit Exit-Code 0 — genau das Muster, vor dem
  [#22](https://github.com/mbalzert1978/fit_back/issues/22) warnt. Wer den Wächter prüfen will,
  löst Fall 1 aus und erwartet die Ablehnung.
- **Der Prozessstart kostet.** Der Wächter läuft bei **jedem** `Edit`/`Write`; ein
  `uv run`-Start liegt laut Messung in #18 bei ~0,9 s.

## Folgen

- Die beiden prozeduralen Gegenmaßnahmen des Vorfalls (`cd`-Weitergabe an Sub-Agenten,
  `git status --short` im Haupt-Checkout) bleiben bestehen. Der Wächter ersetzt sie nicht, er
  fängt ab, was sie durchlassen.
- Die Geometrie bleibt: Worktrees unter `.claude/worktrees/`, ein Claude-Start, Navigation per
  `cd`. Eine Umstellung auf harness-native Isolation wurde erwogen und **nicht** entschieden —
  ob die Kontext-Spiegelung dort greift, ist ungemessen und gehört in ein eigenes Ticket.
