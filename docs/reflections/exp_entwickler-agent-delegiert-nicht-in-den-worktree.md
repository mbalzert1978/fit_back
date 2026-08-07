---
schema_version: 1
name: entwickler-agent-delegiert-nicht-in-den-worktree
description: Ein Entwickler-Agent, der die Arbeit an einen eigenen Sub-Agenten weitergibt, vererbt das Arbeitsverzeichnis nicht - der Sub-Agent laeuft im Haupt-Checkout und committet auf main; der Brief muss Weiterdelegieren ausdruecklich verbieten
type: feedback
frequency: 1
last_triggered: 2026-08-07
decay_eligible: false
---

Ein Implementierungs-Brief, der einen Agenten in einen Worktree schickt, verbietet ihm
**ausdruecklich, die Arbeit an einen eigenen Sub-Agenten weiterzugeben** — und verlangt als ersten
Schritt eine Ausgabe von `pwd` und `git branch --show-current` als Beleg, dass er am richtigen Ort
steht.

**Why:** Der Brief fuer Ticket 0008 sagte in zwei Absaetzen, jeder Shell-Befehl beginne mit einem
expliziten `cd` in den Worktree. Der Agent hat das fuer sich befolgt — und dann entschieden, „den
ganzen Umbau" an einen selbst gestarteten Sub-Agenten zu geben. Der erbte weder den Brief noch das
Arbeitsverzeichnis, lief im Haupt-Checkout und committete `e3121bb` direkt auf `main`, dazu drei
ungetrackte Dateien. Aufgefallen ist es dem Nutzer, nicht mir und keinem Gate. Die Rettung war
billig (`stash` → `cherry-pick` auf den Ticket-Branch → `reset --hard origin/main` → `stash pop`),
haette aber bei einem Push auf `main` oder einem parallelen zweiten Worktree Schaden angerichtet.
Verwandt: [exp_workflow-agent-cd-explizit.md](exp_workflow-agent-cd-explizit.md) — dort ist das
fehlende `cd` das Problem, hier ist es der Empfaenger, der das `cd` nie zu sehen bekam.

**How to apply:** In jeden Worktree-gebundenen Implementierungs-Brief zwei Saetze aufnehmen:
(1) „Du fuehrst diesen Auftrag **selbst** aus. Starte keinen Sub-Agenten und delegiere keinen Teil
der Arbeit weiter — ein Sub-Agent erbt dein Arbeitsverzeichnis nicht und landet im Haupt-Checkout."
(2) „Erster Schritt, vor allem anderen: `pwd` und `git branch --show-current` ausgeben und das
Ergebnis im Bericht zeigen. Stimmt es nicht mit dem Worktree-Pfad und dem Ticket-Branch ueberein,
brich ab und melde." Nach dem Lauf zusaetzlich `git log origin/main..main` im Haupt-Checkout
pruefen — ein leeres Ergebnis ist der Beleg, dass nichts danebengegangen ist.
