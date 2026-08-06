---
schema_version: 1
name: keine-vorpruefung-wo-die-gegenseite-entscheidet
description: Ein Pruefschritt vor dem Schreibschritt macht das Wettrennen erst auf, das er verhindern soll - wo eine Invariante von aussen durchgesetzt wird, liest man ihr Urteil aus dem Ergebnis der eigentlichen Operation
type: feedback
frequency: 1
last_triggered: 2026-08-06
decay_eligible: true
---

Wird eine Invariante von einer Instanz **durchgesetzt** (Unique-Index,
Reservierungssystem, externe API), fragt der Slice sie nicht vorher. Er fuehrt
die Operation aus und liest das Urteil aus deren Ergebnis. Eine vorgelagerte
Abfrage ist nur dann legitim, wenn sie etwas beantwortet, das sich waehrend des
Vorgangs nicht aendern kann.

**Why:** Die Naht des Referenz-Slice hatte zwei Operationen -
`find_by_email(...)` und danach `insert(...)`. Das ist TOCTOU per Konstruktion:
zwischen Pruefung und Schreiben passt jeder nebenlaeufige Vorgang. Der Beweis
stand im eigenen Code: ich musste einen zusaetzlichen Naht-Fall
`WriteCollision` erfinden, um das Rennen abzufangen, das der erste Schritt
ueberhaupt erst geoeffnet hatte - und danach einen Spec fuer ein Problem
schreiben, das ohne ihn nicht existiert. Der Nutzer im Review: *"wieso claim?
das wird ein race einfach user add und wenn email taken dann das melden vom
repo. 2 step ist noise"*. Die Korrektur war reine Loeschung: zwei Port-
Operationen, eine Ergebnis-Union, eine Domaenen-Operation samt Modul, ein
Naht-Fall, eine Test-API-Methode und ein Spec sind ersatzlos verschwunden.

**How to apply:** Beim Entwurf jeder Naht pruefen, ob eine Operation nur
*fragt*, was eine spaetere Operation ohnehin *entscheidet*. Diagnose-Signal: ein
Ergebnis-Fall, den es nur gibt, weil zwei Schritte auseinanderliegen (`…Collision`,
`…Conflict`, `…ChangedMeanwhile`) - das ist kein Fachfall, das ist die Quittung
fuer den ueberfluessigen Schritt. Festgehalten in
`.rules/python/python-feature-slices.md`, Abschnitt „Eine Frage, die nur die
Gegenseite beantworten kann, wird nicht vorab gestellt".
