---
schema_version: 1
name: push-main-before-worktree-fanout
description: Ein lokal committeter, aber ungepushter main-Commit taucht als Scope-Creep im Diff jedes danach erstellten Worktree-Branches/PRs auf - main immer pushen bevor Worktrees fuer eine neue Welle erstellt werden
type: project
frequency: 1
last_triggered: 2026-08-05
decay_eligible: false
---

Wird ein Commit auf `main` gemacht (z. B. Tickets von `blocked` auf `open` setzen), aber nicht
sofort gepusht, bevor neue Worktrees/Branches davon abgezweigt werden, erscheinen dessen Aenderungen
im PR-Diff jedes neuen Branches gegen `origin/main` - selbst wenn sie inhaltlich nichts mit dem
jeweiligen Ticket zu tun haben.

**Why:** Der Unblock-Commit fuer Welle 3 (Tickets 0006-0010 `blocked` -> `open`) wurde committet,
aber nicht gepusht, bevor die Worktrees fuer 0006/0007/0009 erstellt wurden. Dadurch zeigten alle
drei PRs (#6, #7, #8) die Status-Aenderungen aller fuenf Tickets im eigenen Diff, was der Reviewer
mehrfach als "bitte schliessen"/Scope-Creep bemaengelte, bevor der eigentliche Root Cause (main
nicht gepusht) erkannt und behoben wurde.
**How to apply:** Nach jedem Commit auf `main`, der eine neue Welle vorbereitet (Ticket-Status,
gemeinsame Configs), sofort `git push` ausfuehren, bevor `worktree-erstellen` fuer die Welle
aufgerufen wird. Taucht trotzdem unerwarteter Scope-Creep im PR-Diff auf: zuerst `git log
origin/main..main` pruefen, nicht sofort am eigenen Branch herumdebuggen.
