# `claude-doctor` ist Python, `docs/claude/` ist nur ein Wegweiser — und die Map endet

**Datum:** 2026-08-14, 14:08
**Ticket:** [#24 — Ecosystem-Einrichtung dokumentieren und pruefbar machen](https://github.com/mbalzert1978/fit_back/issues/24)
**Map:** [#25 — Hook-Portfolio und semble-Anbindung des Claude-Setups](https://github.com/mbalzert1978/fit_back/issues/25)

## 1. Die Prüfung ist Python, das `make.ps1`-Target nur die Hülle

Das Ticket verlangt `./make.ps1 claude-doctor`. Die Logik dahinter — JSON parsen, Hook-Kommandos
einsammeln, Pfade auflösen — liegt trotzdem in
[`scripts/claude_doctor.py`](../../scripts/claude_doctor.py); das Target ist eine Zeile, die es über
`uv run` aufruft.

Grund: **auf dieser Maschine gibt es kein `pwsh`** (der Befund steht schon in der Map, aufgetaucht in
[#16](https://github.com/mbalzert1978/fit_back/issues/16)). Hätte die Prüflogik in PowerShell
gestanden, wäre sie hier weder ausführbar noch prüfbar gewesen — ein Doktor, den man nicht
untersuchen kann. In Python ließ sie sich sowohl positiv (läuft grün gegen das echte Repo) als auch
negativ (fehlendes Werkzeug, fehlende Settings-Datei, ins Leere zeigende Hook-Referenz) belegen.
Das Skript trägt dafür ein `--demo`-Selbstcheck.

**Nicht verifiziert:** die PowerShell-Hülle selbst. Ohne `pwsh` konnte `./make.ps1 claude-doctor`
hier nicht laufen — geprüft ist die Prüfung, nicht der Aufruf drumherum.

Geprüft wird bewusst wenig: `uv`, `gh`, `semble` auf dem PATH, die beiden Settings-Dateien lesbar,
und jede `$CLAUDE_PROJECT_DIR/…`-Referenz in einem Hook-Kommando existiert. Kein Agenten-, kein
Skill-, kein Versions-Check — die gibt es erst, wenn etwas daran real kaputtgeht.

## 2. `docs/claude/README.md` beschreibt die Pipeline nicht — es zeigt auf sie

Das Ticket formuliert „beschreibt den Pipeline-Ablauf". Wörtlich umgesetzt wäre das eine zweite
Beschreibung neben [`.claude/agents/fit-back-teamlead.md`](../../.claude/agents/fit-back-teamlead.md),
in der sie ausgeführt wird — genau die Doppelung, die
[das Decision-Doc vom 2026-08-13](2026-08-13-1221-claude-md-behauptet-nichts-mehr.md) für `CLAUDE.md`
abgeräumt hat. Die neue Datei nennt die Kette deshalb als eine Zeile und verlinkt für alles Weitere
die Agentendatei; ihr eigener Beitrag ist die Tabelle „was liegt wo und wer liest es", die es bisher
nirgends gab. `CLAUDE.md` verlinkt sie.

## 3. Die Map #25 ist damit zu Ende

[Das Decision-Doc vom 2026-08-14, 06:55](2026-08-14-0655-adr-cluster-faellt-und-die-map-bekommt-ein-ende.md)
hat festgelegt: nach #16, #19 und #24 wird die Map geschlossen, der Nebel bleibt geleert. #16 und #19
sind erledigt, #24 ist es mit diesem Doc. Die Map wird geschlossen; kommt eine der alten
Nebelfragen zurück, entsteht sie als normales Ticket neu, nicht als Fortsetzung.
