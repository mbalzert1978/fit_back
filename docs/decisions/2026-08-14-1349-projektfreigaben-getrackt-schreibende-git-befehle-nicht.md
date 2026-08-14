# Projekt-Freigaben werden getrackt — schreibende Git-Befehle nicht

**Datum:** 2026-08-14, 13:49
**Ticket:** [#16 — Permissions bereinigen und ins getrackte Settings heben](https://github.com/mbalzert1978/fit_back/issues/16)
**Map:** [#25 — Hook-Portfolio und semble-Anbindung des Claude-Setups](https://github.com/mbalzert1978/fit_back/issues/25)

## Was entschieden wurde

**1. Die wiederkehrenden Projekt-Freigaben stehen jetzt in `.claude/settings.json`**, also getrackt
und damit auch in einem frischen Worktree gültig: `uv run`, `./make.ps1`, die lesenden Git-Befehle
(`status`, `diff`, `log`), `gh pr` sowie `gh issue view` / `gh issue list`. Die beiden
`gh issue`-Einträge standen nicht im Ticket — sie sind rein lesend und wurden allein während der
Auflösung dieses Tickets dreimal gebraucht; die Wayfinding-Operationen aus
[`docs/agents/issue-tracker.md`](../agents/issue-tracker.md) laufen ausschließlich darüber.

**2. `git add`, `git commit` und `git checkout` bleiben in `settings.local.json`** — bewusst gegen
den Ticket-Text, der sie nicht ausnahm, aber auch nicht ausdrücklich mitheben wollte. Sie schreiben.
Dieses Repo hat zwei festgehaltene Vorfälle mit Agenten, die an der falschen Stelle committet haben
([Direkt auf `main`](2026-08-05-1045-incident-agent-commit-direkt-auf-main.md),
[Subagent im Haupt-Checkout](2026-08-07-1416-incident-subagent-schreibt-im-haupt-checkout.md)).
Eine repo-weite, in jedem frischen Worktree greifende Auto-Freigabe fürs Committen zeigt genau in
die Richtung, aus der beide Vorfälle kamen. Der Preis ist ein Prompt pro Maschine — billiger als der
nächste Vorfall.

**3. Entfernt:** `Bash(dotnet build *)` und `Bash(dotnet test *)` (Reste der C#-Herkunft),
`Bash(bash .claude/hooks/session-state-handler.sh)` (der Hook ist seit Langem
`session-state-handler.py` und wird über `uv run` gestartet, siehe `.claude/settings.json`) sowie
`Bash(xargs cat -n)` (weder maschinenspezifisch noch wiederkehrend).

## Was dabei aufgefallen ist

**`./make.ps1` läuft auf dieser Maschine nicht.** `pwsh` ist nicht installiert und die Datei ist
nicht ausführbar (`-rw-r--r--`), obwohl `CLAUDE.md` sie als kanonischen Task-Runner führt. Das
Abnahmekriterium des Tickets („ein frischer Worktree kommt ohne neue Permission-Prompts durch
`./make.ps1 ci`") war deshalb nicht wörtlich prüfbar. Ersatzweise wurden die vier Schritte, die
`ci` aufruft, direkt ausgeführt — `ruff check`, `ruff format --check`, `lint-imports`, `pytest` —
alle ohne Permission-Prompt, die ersten drei grün. `pytest` meldet 57 bestanden und 223 Fehler,
sämtlich Testcontainers-Setups ohne laufenden Docker-Daemon; das ist eine Umgebungsbedingung, kein
Befund dieses Tickets.

Die Freigabe `Bash(./make.ps1:*)` bleibt trotzdem stehen: sie gilt dem Repo, nicht dieser Maschine.
