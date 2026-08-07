---
schema_version: 1
name: entwickler-agent-delegiert-nicht-in-den-worktree
description: Ein Sub-Agent erbt das Arbeitsverzeichnis nicht und landet im Haupt-Checkout - Delegieren bleibt erlaubt, aber nur mit weitergereichter cd-Anweisung und einem eigenen Arbeitspaket beim Delegierenden
type: feedback
frequency: 2
last_triggered: 2026-08-07
decay_eligible: false
---

Ein Implementierungs-Brief, der einen Agenten in einen Worktree schickt, **verbietet das
Delegieren nicht** — Parallelitaet ist ausdruecklich gewollt. Er bindet sie an zwei Bedingungen:

1. **Ortsangabe wird weitergereicht.** Jeder Prompt an einen Sub-Agenten beginnt mit derselben
   woertlichen `cd <worktree>`-Anweisung, die der Elternteil bekommen hat — als zu kopierender
   Textbaustein, nicht als Beschreibung („gib den Pfad mit"), weil eine Beschreibung Spielraum
   fuer Abkuerzung und relative Pfade laesst. Ein Sub-Agent startet keine weiteren Sub-Agenten;
   ab Ebene 3 ist die Ortsangabe nicht mehr kontrollierbar.
2. **Delegieren heisst parallel arbeiten, nicht dirigieren.** Wer Arbeit abgibt, behaelt
   gleichzeitig ein eigenes Arbeitspaket. Vier Sub-Agenten beauftragen und dann warten ist keine
   Parallelisierung, sondern eine Ebene Latenz und eine Ebene Kontrollverlust ohne Gegenwert.
   Der Schnitt ist disjunkt (paarweise ueberschneidungsfreie Dateimengen) und steht fest, **bevor**
   der erste Sub-Agent startet.

**Why:** Zweimal an zwei Tagen dasselbe Muster. Bei Ticket 0008 gab der Agent „den ganzen Umbau"
an einen Sub-Agenten, der im Haupt-Checkout `e3121bb` direkt auf `main` committete. Bei Ticket
0048 hielt sich der Agent selbst korrekt an sein `cd`, startete aber fuer die 45 `D103`/`D104`-
Verstoesse einen Sub-Agenten, der ohne Ortsangabe 34 Dateien im Haupt-Checkout aenderte — diesmal
ohne Commit, weil rechtzeitig gestoppt. Beide Male fiel es dem Nutzer auf, keinem Gate.

Die erste Fassung dieser Reflection zog daraus das Verbot von Sub-Agenten. Der Nutzer hat das
verworfen: das Problem ist die fehlende Ortsangabe nach unten und der Leerlauf oben, nicht die
Delegation. Ein Verbot haette den erwuenschten Nutzen mitgenommen und die eigentliche Ursache
zugedeckt. Details:
[docs/decisions/2026-08-07-1416-incident-subagent-schreibt-im-haupt-checkout.md](../decisions/2026-08-07-1416-incident-subagent-schreibt-im-haupt-checkout.md).

**How to apply:** Beide Bedingungen als eigenen Abschnitt in jeden Worktree-gebundenen Brief,
mit abhakbarem Fertig-Kriterium statt als Appell: woertliche `cd`-Anweisung je Sub-Agent ·
disjunkte Dateimengen · eigenes Paket waehrend der gesamten Laufzeit · nach dem Zusammenfuehren
`git status --short` im **Haupt-Checkout** leer. Der letzte Punkt ist die Kontrolle, die beide
Vorfaelle gefunden haette, und er greift auch bei Fehlern, die die ersten drei nicht abdecken —
deshalb nach *jedem* Worktree-Agentenlauf fahren, nicht nur bei Verdacht. Laesst sich die Arbeit
nicht disjunkt schneiden, wird nicht delegiert. Verwandt:
[[workflow-agent-cd-explizit]], [[agenten-instruktionen-ueber-refine-prompt]],
[[hintergrund-agent-delegiert-nicht-weiter]].
