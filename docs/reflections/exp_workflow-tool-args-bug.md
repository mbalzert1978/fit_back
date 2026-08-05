---
schema_version: 1
name: workflow-tool-args-bug
description: Das Workflow-Tool liefert args manchmal als undefined ins Skript - Eingabedaten als literales const hardcoden statt args nutzen
type: project
frequency: 1
last_triggered: 2026-08-05
decay_eligible: false
---

Das an `Workflow(...)` uebergebene `args`-Objekt kam im Skript-Body zweimal als
`undefined` an (reproduziert sowohl bei einem frischen Lauf als auch via
`resumeFromRunId`), obwohl es syntaktisch korrekt als JSON-Objekt/Array uebergeben
wurde — sofortiger Fehler wie `args.tickets ist undefined`.

**Why:** Ungeklaerter Bug im Workflow-Tool dieser Session, nicht auf einen
Bedienfehler zurueckgefuehrt (Syntax war laut Tool-Doku korrekt). Der einzige
verlaessliche Workaround war, die Ticket-/Eingabedaten als literales `const`
direkt im Skript-Body zu hardcoden statt sich auf den `args`-Mechanismus zu
verlassen.

**How to apply:** Bei jedem kuenftigen Workflow-Skript fuer diese Pipeline (oder
generell, wenn `args` in einem neuen Skript benoetigt wird) zunaechst mit einem
minimalen Testlauf verifizieren, dass `args` tatsaechlich ankommt, bevor darauf
aufgebaut wird — im Zweifel sofort auf die Hardcode-Variante ausweichen, statt
Zeit mit wiederholten Retries zu verlieren.
