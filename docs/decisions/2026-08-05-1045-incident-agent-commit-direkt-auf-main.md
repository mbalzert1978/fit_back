# Incident: Fix-Agent committet direkt auf main statt im Worktree

**Entschieden:** 2026-08-05 10:45

## Was

Waehrend der Welle-2-Batch-1-Pipeline (Ticket 0002) hat ein Security-Fix-Agent seine
Aenderungen nicht im zugewiesenen Worktree (`.claude/worktrees/0002-ruff-import-linter`,
Branch `0002-ruff-import-linter`) committet, sondern direkt im Haupt-Checkout auf `main`
(Commit `96b8f2c`, „Fix security findings: add rate limiting, CSRF protection, input
validation, and error handling"). Dieser Commit landete ohne QA-Gate, ohne Security-Gate,
ohne PR und ohne Stakeholder-Review direkt auf `main` — inklusive der zu diesem Zeitpunkt
noch ungefixten SECRET_KEY-Default-Schwachstelle. Dadurch geriet PR #4 (Ticket 0002) in
einen echten Merge-Konflikt in `main.py`, weil `main` und der `0002`-Branch unabhaengig
voneinander denselben Codeabschnitt veraendert hatten.

**Bereinigung:** `git revert 96b8f2c` direkt auf `main` (per Nutzerentscheidung, Option
„Rogue-Commit revert + SECRET_KEY-Fix direkt auf main"), gepusht als `4165fed`. Da die
CSRF-Middleware/`SECRET_KEY`-Logik ausschliesslich durch die Entwicklung von Ticket 0002
eingefuehrt wurde (nicht Teil der Ticket-0001-Baseline), stellt der Revert `main.py`
exakt auf den Ticket-0001-Endstand zurueck — es existiert danach keine
CSRF/SECRET_KEY-Logik mehr auf `main`, also auch keine dort verbliebene Schwachstelle.
Kein weiterer Patch auf `main` noetig. PR #4 ist danach wieder `MERGEABLE`/`CLEAN`
(verifiziert per `gh pr view 4 --json mergeable,mergeStateStatus`).

## Warum (Root Cause)

Die Workflow-Pipeline-Prompts (siehe `wave2-batch1.js`) haben jedem Agenten das
Arbeitsverzeichnis nur als **Kontext-Text** mitgegeben ("Im Worktree {dir} (Branch
{branch})"), aber nie eine explizite Anweisung, tatsaechlich dorthin zu wechseln (`cd`),
bevor Git-Kommandos ausgefuehrt werden. Ein Agent hat daraufhin vermutlich in seinem
Default-Arbeitsverzeichnis (dem Haupt-Checkout) `git add`/`git commit`/`git push`
ausgefuehrt — mit fatalen Folgen, weil dieses Verzeichnis zufaellig `main` ausgecheckt
hatte.

Das ist der **zweite** Pipeline-Integritaets-Vorfall dieser Welle, nach der
Config-Selbstmodifikation aus
[`2026-08-05-1130-security-gate-triage-ticket-0002-und-agent-integritaets-incident.md`](2026-08-05-1130-security-gate-triage-ticket-0002-und-agent-integritaets-incident.md).
Beide Vorfaelle sind Prozess-/Vertrauensprobleme der Pipeline selbst, keine fachlichen
Trade-offs — deshalb hier explizit dem Stakeholder gemeldet statt eigenmaechtig
kleingeredet.

## Was das ausschliesst / verbindliche Folgemassnahme

- **Verbindlich ab sofort fuer jeden kuenftigen Workflow-Pipeline-Prompt:** jeder
  agent()-Aufruf, der Git-Kommandos im Kontext eines Tickets ausfuehrt, muss den
  Worktree-Pfad nicht nur nennen, sondern eine **explizite Anweisung enthalten,
  zuerst dorthin zu wechseln** (z. B. `cd <pfad>` als expliziter erster Schritt im
  Prompt, nicht nur als Kontextsatz) — sowie idealerweise eine Selbstverifikation
  (`git branch --show-current` pruefen == erwarteter Branch, bevor committet wird).
  Fuer Welle 2 Batch 2 (Ticket 0005) war die Pipeline zum Zeitpunkt dieses Vorfalls
  bereits gestartet (In-Memory-Prompts koennen waehrend eines laufenden
  Workflow-Runs nicht mehr nachtraeglich gehaertet werden) — nach Abschluss von
  Batch 2 verifiziert, dass kein weiterer Rogue-Commit auf `main` gelandet ist
  (`git log --oneline` auf `main` blieb sauber bei `4165fed`).
  Jeder kuenftige Workflow-Skript-Entwurf (Welle 3 und folgende) muss diese Haertung
  bereits im Prompt-Text tragen.
- Aendert nichts an Inhalt/Umfang von Ticket 0002 selbst — der fachliche Code in PR #4
  bleibt unveraendert, nur `main` wurde bereinigt.
