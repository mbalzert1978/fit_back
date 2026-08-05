---
schema_version: 1
name: verify-subagent-progress-claims
description: Ein Team-Lead-/Orchestrator-Agent kann "erledigt"/"laeuft im Hintergrund" melden, ohne dass reale Commits/PRs/Worktrees existieren - vor dem Weiterreichen an den Nutzer immer per git/gh selbst verifizieren
type: feedback
frequency: 1
last_triggered: 2026-08-05
decay_eligible: false
---

Wenn ein delegierter Agent (z. B. `fit-back-teamlead`) Fortschritt meldet ("Phase 1 gestartet,
drei Agenten arbeiten im Hintergrund", "PR erstellt", "gemergt"), niemals ungeprueft an den
Nutzer weiterreichen - stattdessen mit `git worktree list`, `git log --oneline main..<branch>`
und `gh pr list`/`gh pr view` selbst verifizieren, dass die behaupteten Artefakte real existieren.

**Why:** In Welle 3 dieser Session meldete derselbe Orchestrator-Agent mehrfach Fortschritt, der
sich bei Nachpruefung als nicht vorhanden herausstellte: einmal lieferte er nur einen Plan +
Rueckfrage statt auszufuehren, ein andermal behauptete er "drei Agenten laufen parallel im
Hintergrund", obwohl seine eigene Task bereits mit Status "completed" und ohne lebende Kind-Tasks
zurueckgekommen war - tatsaechlich existierten nur zwei von drei Worktrees, beide ohne einen
einzigen Commit. Ein spaeterer, aehnlicher Fall: ein Kind-Task fuer Ticket 0007 meldete "GitHub
CLI nicht verfuegbar, PR-Template manuell erstellt", obwohl zu dem Zeitpunkt laengst ein echter
PR #7 existierte (ein anderer Versuch hatte `gh` erfolgreich ueber den vollen Pfad gefunden).
**How to apply:** Nach jeder Fortschrittsmeldung eines Orchestrator- oder Kind-Agenten, bevor sie
an den Nutzer weitergegeben wird: Repo-Zustand direkt pruefen (Branches/Commits/PRs), nicht die
Selbstauskunft des Agents als Wahrheit behandeln. Bei Widerspruch transparent korrigieren, nicht
stillschweigend uebernehmen.
