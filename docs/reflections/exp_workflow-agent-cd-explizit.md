---
schema_version: 1
name: workflow-agent-cd-explizit
description: Workflow-Pipeline-Prompts fuer Git-Operationen brauchen ein explizites cd, nicht nur den Worktree-Pfad als Kontext
type: feedback
frequency: 1
last_triggered: 2026-08-05
decay_eligible: false
---

Jeder `agent()`-Aufruf einer Workflow-Pipeline, der Git-Kommandos im Kontext eines
Tickets ausfuehrt, muss den Worktree-Pfad nicht nur als Kontext-Satz nennen
("Im Worktree {pfad} (Branch {branch})"), sondern eine **explizite Anweisung**
enthalten, zuerst dorthin zu wechseln (`cd {pfad}` als expliziter erster Schritt),
idealerweise mit Selbstverifikation (`git branch --show-current` gegen den
erwarteten Branch pruefen, bevor committet wird).

**Why:** Ein Fix-Agent in der Welle-2-Pipeline hat seine Aenderungen direkt im
Haupt-Checkout auf `main` committet statt im zugewiesenen Worktree — der Prompt
nannte den Pfad nur als Kontext, nie als Handlungsanweisung. Der Commit landete
dadurch ohne QA-/Security-Gate und ohne PR direkt auf `main`. Details:
[docs/decisions/2026-08-05-1045-incident-agent-commit-direkt-auf-main.md](../decisions/2026-08-05-1045-incident-agent-commit-direkt-auf-main.md).

**How to apply:** Bei jedem neuen Workflow-Skript fuer diese Ticket-Pipeline
(Welle 3 und folgende) diese Haertung von Anfang an in `devPrompt`/`fixPrompt`/
`securityPrompt` einbauen, nicht erst nachtraeglich nach einem Vorfall.
