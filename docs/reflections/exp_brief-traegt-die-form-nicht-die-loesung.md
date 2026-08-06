---
schema_version: 1
name: brief-traegt-die-form-nicht-die-loesung
description: Ein Implementierungs-Brief an einen Agenten beschreibt, WAS gelten muss (Regel, Zielform, Fertig-Kriterium) - nie WIE das Problem zu loesen ist; eine konkrete Loesungsvorgabe schlaegt jeden Regel-Verweis und macht den Denkfehler des Auftraggebers unkorrigierbar
type: feedback
frequency: 2
last_triggered: 2026-08-06
decay_eligible: false
---

Ein Brief an einen Implementierungs-Agenten formuliert die **Form**: welche Regel gilt, welche
Zielstruktur, welches Fertig-Kriterium. Er formuliert **nie die Loesung** — nicht „definiere einen
`LocalizationPort` im shared_kernel", sondern „`domain/` haengt nur an der stdlib; die
Review-Checkliste aus `python-feature-slices.md` ist Punkt fuer Punkt das Fertig-Kriterium". Das
*Wie* leitet der Agent aus der Regel ab.

**Why:** Bei den Fix-Auftraegen fuer PR #9/#10 stand im selben Prompt ein Verweis auf `.rules/` UND
eine konkrete, widersprechende Anweisung von mir („definiere einen Protocol-Port im shared_kernel
und injiziere den ResourceProvider"). Der Agent folgte der konkreten Anweisung — korrekt von ihm,
denn konkrete Anweisung schlaegt Verweis immer. Meine Anweisung war aber strukturell falsch: sie
fuegte Indirektion hinzu, um eine falsche Platzierung zu konservieren, statt die Framework-
Abhaengigkeit aus der Domaene zu entfernen. Der Nutzer fing das ab („wieso ist das im shared
kernel? das ist klar infrastruktur"), nicht das Gate und nicht der Agent — der hatte keine
Moeglichkeit mehr dazu, weil ich seine Urteilsfaehigkeit vorweggenommen hatte. Siehe
[exp_regel-lesen-bevor-referenzieren.md](exp_regel-lesen-bevor-referenzieren.md) fuer die
Vorstufe desselben Fehlers.

**How to apply:** Vor jedem `agent()`-Aufruf, der Code aendern soll, den eigenen Prompt gegenlesen:
Steht darin ein Satz, der eine konkrete Struktur-Entscheidung vorwegnimmt („definiere X", „baue
einen Adapter Y", „verschiebe nach Z")? Dann streichen und durch die Regel + das pruefbare
Fertig-Kriterium ersetzen. Zulaessig bleiben: Zielablage, Layer-Constraints, Naht-Vertraege,
woertliche Review-Checklisten, Abgrenzung („NICHT tun"). Unzulaessig: der Loesungsweg.
