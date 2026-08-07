---
schema_version: 1
name: reviewer-gegen-veralteten-main-diffen
description: Waehrend ein Ticket laeuft auf main zu committen und den Reviewer dann main..branch diffen zu lassen erzeugt Phantom-Findings - die neuen main-Commits erscheinen als Loeschungen im Branch
type: feedback
frequency: 1
last_triggered: 2026-08-07
decay_eligible: false
---

Bevor ein diff-basierter Reviewer auf einen Ticket-Branch losgelassen wird, muss der
Vergleichspunkt stimmen: entweder **`main` vorher in den Branch mergen** oder den Reviewer
gegen die **Merge-Base** diffen lassen (`git merge-base main <branch>`), nie gegen ein `main`,
das seit dem Abzweig weitergelaufen ist.

**Why:** Waehrend Ticket 0048 lief, habe ich drei Doku-Commits auf `main` gelegt (Reflections,
Decision-Doc, `issue-close` fuer 0008) und danach das QA-Gate mit dem Scope
`git diff main..0048-ruff-production-level` gestartet. Der Reviewer meldete `Verdict: BLOCK`
mit zwei Findings: „Issue 0008 von closed auf open zurueckgesetzt" und „vier Doc-Dateien
geloescht". Beides war korrekt gelesen und trotzdem falsch — es waren meine eigenen
main-Commits, die dem Branch schlicht fehlten. Gegen die Merge-Base war der `docs/`-Diff des
Branches leer. Kosten: ein BLOCK-Urteil, das erst widerlegt werden musste, plus die Gefahr,
dass ein echtes drittes Finding im Rauschen untergeht.

**How to apply:** Vor jedem Dispatch eines diff-basierten Gates einmal
`git diff --stat $(git merge-base main <branch>)..<branch>` gegen
`git diff --stat main..<branch>` halten. Weichen sie ab, ist `main` weitergelaufen — dann
erst mergen, dann dispatchen. Und generell: waehrend ein Ticket im Gate steht, nicht
nebenher auf `main` committen; sind die Commits unvermeidlich (Doku, Vorfallsbericht), gehoert
der Merge in den Branch unmittelbar danach, nicht erst wenn ein Reviewer stolpert. Verwandt:
[[pruefkommando-muss-messen-was-es-behauptet]], [[push-main-before-worktree-fanout]].
