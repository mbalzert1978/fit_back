---
schema_version: 1
name: baseline-begruendung-ist-eine-vermutung
description: Die Begruendung, die beim Einfrieren einer Lint-/Typechecker-Baseline notiert wird, ist eine Vermutung und keine Diagnose - beim Abbau wird die Ursache neu gemessen, nie uebernommen
type: project
frequency: 1
last_triggered: 2026-08-26
decay_eligible: true
---

Wer eine Zeile aus einer eingefrorenen Baseline (`[[tool.ty.overrides]]`, `# noqa`-Listen,
Suppression-Dateien) abbaut, **misst die Ursache neu**. Die dort notierte Begruendung ist ein
Ausgangspunkt fuer die Suche, nie ihr Ergebnis — auch dann nicht, wenn sie praezise klingt und
Klassennamen nennt.

**Why:** Beim Abbau der `ty`-Baseline (Issue #97, 37 Befunde in 18 Dateien) war die eingetragene
Begruendung **viermal falsch**, und zwar auf eine Art, die ohne Nachmessen nicht auffaellt: Welle 1
war keine Werkzeug-Luecke, sondern Invarianz in `result.py`; Welle 2 lag an der verschachtelten
Musterform, nicht an `Err[E]`; Welle 3 im Outbox-Worker nicht am Lebenszyklus, sondern an einem
real erreichbaren `None`-Zweig; Welle 5 nannte `StreamingResponse`, wo es der private
`_StreamingResponse` war, der gar nicht davon erbt. Von 37 eingefrorenen Befunden war am Ende
**keiner** eine Werkzeug-Macke. Der Grund ist strukturell: eine Baseline-Begruendung entsteht unter
Zeitdruck, in genau dem Moment, in dem man den Befund *nicht* untersucht — und liest sich spaeter
wie ein Befund. Hergang: `docs/decisions/2026-08-25-1500-typechecker-ty.md`.

**How to apply:** Beim Einfrieren die Begruendung als das kennzeichnen, was sie ist („vermutet:
…"), nicht als Diagnose. Beim Abbau zuerst gegen eine **override-freie** Konfiguration messen (die
Baseline versteckt genau die Befunde, um die es geht), dann die vermutete Ursache mit einer
minimalen Sonde isolieren, und erst danach reparieren. Faellt eine Zeile, gehoert die *korrigierte*
Ursache ins Decision-Doc — inklusive der Feststellung, dass die alte falsch war; sonst wandert der
Irrtum in die naechste Baseline. Verwandt:
[exp_schweigen-des-typpruefers-ist-kein-freispruch.md](exp_schweigen-des-typpruefers-ist-kein-freispruch.md).
