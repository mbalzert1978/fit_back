---
schema_version: 1
name: zweifelsfaelle-bericht-deckt-regel-luecken-auf
description: Ein Agenten-Brief, der einen Bericht ueber die Stellen verlangt, an denen der Agent entscheiden musste ohne dass es eindeutig aus der Regel folgte, deckt zuverlaessig die Luecken in der eigenen Regel auf - das ist der billigste verfuegbare Regel-Test
type: feedback
frequency: 1
last_triggered: 2026-08-06
decay_eligible: true
---

Jeder Brief, der einen Agenten eine Regel anwenden laesst, verlangt am Ende verpflichtend eine
Liste der Stellen, an denen der Agent **entscheiden musste, ohne dass die Entscheidung eindeutig
aus der Regel folgte** — mit dem ausdruecklichen Zusatz, das ehrlich zu melden statt zu glaetten.
Diese Liste ist kein Nebenprodukt, sondern der eigentliche Test der Regel.

**Why:** Bei der Umstellung von 36 Tickets auf die gestufte Slice-Form durch fuenf
Sonnet-Chargen deckte genau dieser Berichtsteil **vier echte Luecken** in einer frisch
geschriebenen Regel auf: (1) der Fall „Use Case ohne HTTP-Oberflaeche" (zwei statt drei Stufen)
war nicht definiert; (2) die Formulierung „ein Ticket je Use Case" suggerierte faelschlich, ein
Ticket duerfe nur einen Use Case enthalten — daraufhin legte ein Agent Abfrage und Kommando zu
`get_and_update_goals` zusammen, statt zwei Slices zu bauen; (3) Queries ohne eigenes Aggregat
waren nicht abgedeckt; (4) die Abgrenzung „Fachregel vs. reine Technik" wurde von zwei Agenten
unterschiedlich beurteilt. Alle vier wurden von den Agenten selbst als Zweifelsfall gemeldet und
nicht versteckt. Ohne diese Berichtspflicht waeren sie als stille Fehlinterpretationen in 36
Dateien gelandet. Setzt [exp_brief-traegt-die-form-nicht-die-loesung.md](exp_brief-traegt-die-form-nicht-die-loesung.md)
voraus: nur wer die Form statt der Loesung vorgibt, bekommt ueberhaupt brauchbare Zweifelsfaelle
zurueck.

**How to apply:** In den `## Bericht`-Abschnitt jedes Implementierungs- oder
Umstrukturierungs-Briefs aufnehmen: „plus eine Liste der Stellen, an denen du unsicher warst oder
eine Entscheidung treffen musstest, die **nicht eindeutig aus der Form folgte**. Dieser Teil ist
wichtig — er deckt Luecken in der Regel auf, also melde ihn ehrlich statt ihn zu glaetten." Die
gemeldeten Zweifelsfaelle danach **zuerst** abarbeiten (Regel nachschaerfen), erst dann die
Arbeitsergebnisse durchsehen — eine Regel-Luecke wiederholt sich sonst in jeder folgenden Charge.
