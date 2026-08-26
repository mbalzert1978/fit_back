---
schema_version: 1
name: subagenten-mechanismus-behauptung-nachmessen
description: Ein Subagent kann korrekte Arbeit mit einer falschen Ursachen-Erklaerung abliefern - bevor eine solche Erklaerung in ein Issue oder Decision-Doc wandert, wird sie mit einer eigenen Sonde geprueft
type: feedback
frequency: 1
last_triggered: 2026-08-26
decay_eligible: true
---

Die **Mechanismus-Behauptung** eines Subagenten („das geht nur durch, weil …", „das liegt daran,
dass …") wird selbst nachgemessen, bevor sie weitergereicht wird — auch dann, wenn die gelieferte
Aenderung nachweislich richtig ist. Richtige Arbeit und richtige Begruendung sind zwei getrennte
Behauptungen.

**Why:** Ein Welle-3-Agent lieferte eine sauber korrigierte `db_schemas.py` und begruendete
nebenbei, die nicht-`Mapped`-Annotation gehe dort nur durch, weil Python 3.14 Annotationen
verzoegert auswertet; ohne PEP 649 braeuchte es `__allow_unmapped__`. Der Nutzer uebernahm das
woertlich in den Auftrag fuer ein neues Issue. Eine Sonde (SQLAlchemy 2.0.51 / Python 3.14.5, mit
zur Definitionszeit materialisierten `__annotations__`) zeigte: die Form wird auch dann akzeptiert.
Das Ticket waere mit der Praemisse „wir stehen auf einer Zufaelligkeit" entstanden — falsch, und
dringlicher klingend, als die Lage ist. Es wurde stattdessen auf den belastbaren Grund gestellt
(`nullable=True` ist in dieser Form nicht ausdrueckbar). Siehe Issue #101 und
`docs/decisions/2026-08-25-1500-typechecker-ty.md`.

**How to apply:** Aus einem Subagenten-Bericht ist der *Befund* (Datei, Zeile, Verhalten) das
Belastbare; die *Erklaerung* ist eine Hypothese. Bevor eine Erklaerung in ein Issue, ein
Decision-Doc oder eine Nachricht an den Nutzer geht: kleinste Sonde im Scratchpad, die genau diese
Erklaerung falsifizieren wuerde. Faellt sie durch, wird das Artefakt mit der korrigierten Praemisse
geschrieben **und** die Korrektur benannt — auch wenn der Nutzer die falsche Version selbst zitiert
hat. Verwandt:
[exp_verify-subagent-progress-claims.md](exp_verify-subagent-progress-claims.md) (dort: behaupteter
*Fortschritt*, hier: behaupteter *Mechanismus*).
