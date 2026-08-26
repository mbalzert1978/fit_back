---
schema_version: 1
name: parallele-agenten-brauchen-eigene-worktrees
description: Mehrere Agenten gleichzeitig im selben Working Tree sehen gegenseitig ihre uncommitteten Aenderungen, halten sie fuer eigene Fehler und versuchen destruktiv aufzuraeumen - je Charge ein Worktree, oder zwischen den Chargen committen, oder seriell laufen lassen
type: feedback
frequency: 2
last_triggered: 2026-08-26
decay_eligible: false
---

Werden mehrere Agenten parallel auf denselben Working Tree losgelassen, sieht jeder von ihnen die
uncommitteten Aenderungen aller anderen und kann sie nicht von eigenen Fehlern unterscheiden. Ein
Hinweis im Brief („andere Agenten arbeiten parallel") reicht dafuer **nicht** aus. Zulaessig sind
vier Formen: je Charge ein eigener Worktree, ein Commit zwischen den Chargen, serielle Ausfuehrung
— oder ein **ausgesprochenes Verbot** der git-veraendernden Kommandos im Brief (siehe unten).

**Why:** Beim Fan-out von vier Sonnet-Agenten ueber `docs/issues/` (je eine disjunkte Ticket-Liste,
mit explizitem Parallelitaets-Hinweis im Brief) sah einer der Agenten ~35 geaenderte Dateien,
obwohl er selbst nur sechs angefasst hatte. Er schloss auf einen eigenen Fehler und versuchte
`git restore docs/issues/*.md docs/milestones/00-overview.md` — das haette die Arbeit der drei
anderen Agenten **und** eine unabhaengige Regel-Korrektur vernichtet. Nur der
Sandbox-Sicherheitsmechanismus hat es blockiert; nach unabhaengiger Pruefung war nichts verloren.
Die Ursache lag in der Orchestrierung, nicht beim Agenten: er hat die Lage korrekt als anomal
erkannt und nur die falsche Konsequenz gezogen. Verwandt, aber anderer Mechanismus:
[exp_workflow-agent-cd-explizit.md](exp_workflow-agent-cd-explizit.md) (Agent committet ausserhalb
seines Worktrees).

**How to apply:** Vor jedem Fan-out mit mehr als einem schreibenden Agenten entscheiden: Worktrees
(bei Code, per `worktree-erstellen`-Skill) oder Commit-zwischen-Chargen (bei Dokumenten im
Haupt-Checkout, billiger als Worktrees) oder seriell. Zusaetzlich in jeden Brief eines parallelen
Agenten: **„Wenn du Aenderungen an Dateien siehst, die du nicht angefasst hast, ist das erwartet —
melde es, aber setze nichts zurueck."** Kein `git restore`/`checkout --`/`clean` mit Glob-Mustern
durch einen Subagenten, nie.

**Nachtrag 2026-08-26 (Abbau der `ty`-Baseline, Wellen 2–5).** Die vierte Form ist erprobt: kein
Worktree, alle Agenten im Haupt-Checkout, aber im Brief jedes Agenten woertlich **„Kein `git stash`
/ `git checkout` / `git restore` / `git commit` / `git add` — es arbeiten Agenten parallel im
selben Arbeitsbaum. Vorher/Nachher-Vergleiche nur ueber eine Kopie im Scratchpad."** Der Anlass war
Welle 2 *ohne* diesen Satz: ein Agent fuhr `git stash` + `pop` ueber den ganzen Baum, waehrend ein
zweiter hineinschrieb (nichts ging verloren, unabhaengig geprueft — reines Glueck). Mit dem Satz
liefen die Wellen 3, 4 und 5 sauber. Drei Bedingungen gehoeren dazu, sonst traegt die Form nicht:
**disjunkte Dateimengen** je Agent, **alle git-Operationen beim Orchestrator**, und der Hinweis,
dass fremde Aenderungen im Baum erwartbar sind und zum eigenen Delta nicht zaehlen — die Agenten
melden sonst die Befunde der Nachbarn als eigene Messung. Billiger als Worktrees und ohne deren
Nebenwirkung, dass ein Write-Guard-Hook die Schreibzugriffe blockiert.
