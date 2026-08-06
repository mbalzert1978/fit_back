---
schema_version: 1
name: hintergrund-agent-delegiert-nicht-weiter
description: Ein Hintergrund-Agent, der seinerseits Hintergrund-Arbeit anstoesst und auf deren Ergebnis wartet, endet leer - er bekommt die Benachrichtigung nie, weil sein Prozess mit dem Warten endet
type: project
frequency: 1
last_triggered: 2026-08-06
decay_eligible: true
---

Ein als Hintergrund-Agent gestarteter Subagent muss seine Aufgabe **selbst und
synchron** erledigen. Stoesst er stattdessen weitere Hintergrund-Arbeit an
(Skills, die ihrerseits Agenten spawnen) und wartet auf deren Ergebnis, endet
er sofort mit einer leeren Antwort - das Ergebnis, auf das er wartet, erreicht
ihn nie.

**Why:** In einer Gate-Runde mit fuenf parallelen Sonnet-Agenten bekam einer den
Auftrag, drei Pruef-Skills abzuarbeiten. Er invokierte alle drei, diese starteten
ihrerseits Hintergrund-Agenten, und er meldete zurueck: *„Ich warte auf die
Skill-Ergebnisse. Die drei Pruefungen laufen parallel im Hintergrund - die
Ergebnisse kommen als Benachrichtigungen."* Damit war er fertig, ohne eine
einzige Zeile Code angesehen zu haben. Elf Sekunden Laufzeit, null Findings, ein
Bericht, der wie ein Zwischenstand aussah und keiner war. Nach einer
Nachricht mit der Auflage „mach es selbst, delegiere nichts weiter" lieferte
derselbe Agent einen brauchbaren Bericht mit drei Findings.

**How to apply:** In den Auftrag jedes Hintergrund-Agenten hineinschreiben:
*selbst pruefen, synchron, mit Read/Grep/Glob - keine weiteren Agenten starten.*
Skill-Beschreibungen darf er als Checkliste lesen, aber die Arbeit macht er mit
eigenen Augen. Diagnose beim Lesen des Ergebnisses: eine auffaellig kurze
Laufzeit, wenige Tool-Aufrufe und ein Text, der etwas ankuendigt statt zu
berichten - dann ist nichts geprueft worden, und der Agent wird mit dieser
Auflage neu angestossen statt sein Ergebnis weitergereicht. Verwandt:
[[verify-subagent-progress-claims]], [[gruenes-gate-ohne-scope-angabe]].
