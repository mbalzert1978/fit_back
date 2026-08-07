---
schema_version: 1
name: agenten-instruktionen-ueber-refine-prompt
description: Jeder Prompt an einen Agenten laeuft vor dem Start durch den Skill refine-prompt - auch die Prompts, die ein Agent seinerseits an seine Sub-Agenten gibt
type: feedback
frequency: 1
last_triggered: 2026-08-07
decay_eligible: false
---

Agenten werden nicht mit frei formulierten Prompts gestartet. Jeder Auftrag laeuft vorher durch
den Skill `refine-prompt`, und gestartet wird mit dem **zurueckgegebenen** Text, nicht mit dem
Entwurf. Das gilt auf jeder Ebene: auch fuer die Prompts, die ein Entwickler-Agent seinerseits an
Sub-Agenten gibt.

Ausgenommen ist der `cd <worktree>`-Block — er steht woertlich am Anfang und ist nicht Gegenstand
der Ueberarbeitung, sonst formuliert `refine-prompt` genau die Ortsangabe um, die exakt bleiben
muss.

**Why:** Vom Nutzer als Vorgabe gesetzt, nachdem zwei Agentenlaeufe fuer Ticket 0048 an Luecken
im Briefing gescheitert waren, die eine Ueberarbeitung gefunden haette: fehlendes
Fertig-Kriterium je Teilaufgabe, unklare Abgrenzung („was ist ausdruecklich nicht zu tun"),
unbenannte Dateilisten. `refine-prompt` fuehrt den Prompt nicht aus, es gibt nur besseren Text
zurueck — der Durchgang kostet wenig und faengt genau die Stellen ab, an denen ein Agent sonst
raet.

**How to apply:** Vor jedem `Agent`-/`SendMessage`-Start: Entwurf schreiben, `refine-prompt`
darauf anwenden, mit dem Ergebnis starten. In jeden Implementierungs-Brief einen Punkt aufnehmen,
der dieselbe Pflicht an den Agenten weitergibt, mitsamt der Ausnahme fuer den `cd`-Block — und
als abhakbares Fertig-Kriterium formulieren („Jeder Sub-Agent-Prompt lief vor dem Start durch
`refine-prompt`"), nicht als Empfehlung. Verwandt:
[[entwickler-agent-delegiert-nicht-in-den-worktree]], [[brief-traegt-die-form-nicht-die-loesung]].
