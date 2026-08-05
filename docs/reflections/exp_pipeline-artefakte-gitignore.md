---
schema_version: 1
name: pipeline-artefakte-gitignore
description: Pipeline-Arbeitsdateien wie Task.md muessen von Anfang an gitignored sein, sonst leaken sie ueber Squash-Merges in jeden neuen Worktree
type: project
frequency: 1
last_triggered: 2026-08-05
decay_eligible: false
---

Jede Datei, die nur als Arbeitsartefakt der Ticket-Pipeline dient (z. B.
`Task.md`, vom Entwickler-Agenten gelesen, nie fachlicher Repo-Inhalt), muss von
Anfang an in `.gitignore` stehen — bevor die erste Welle sie erzeugt, nicht erst
nachdem sie versehentlich committet wurde.

**Why:** `Task.md` aus Ticket 0001 wurde versehentlich in PR #1 mitcommittet
(kein expliziter `.gitignore`-Eintrag). Nach dem Squash-Merge war sie in `main`
getrackt und tauchte dadurch in **jedem** neu erstellten Worktree-Branch als
bereits vorhandene, veraltete Datei auf (musste per `git rm --cached` + Reset
aller betroffenen Branches bereinigt werden).

**How to apply:** Bevor eine neue Art von Pipeline-Arbeitsdatei eingefuehrt wird
(egal ob Task.md-Nachfolger oder ein neues Format), sofort in `.gitignore`
aufnehmen und mit einem Test-Commit verifizieren, dass sie nicht versehentlich
mit `git add .` erfasst wird.
