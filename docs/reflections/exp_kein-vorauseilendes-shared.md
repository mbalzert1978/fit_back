---
schema_version: 1
name: kein-vorauseilendes-shared
description: Ein `shared/`-Ordner entsteht erst, wenn ein ZWEITER Nutzer existiert - beim ersten Slice gehoert alles in den Slice, egal wie allgemein es wirkt
type: feedback
frequency: 1
last_triggered: 2026-08-06
decay_eligible: true
---

Solange es genau **einen** Slice gibt, gibt es nichts zu teilen. Ein Baustein
wandert erst dann nach oben (`shared_kernel`), wenn ein **zweiter** Slice ihn
tatsaechlich braucht - und bekommt dort dieselbe Behandlung wie jeder andere
Port: Naht plus Adapter, nicht direkt verdrahtet.

**Why:** Beim Bau des Referenz-Slice (Ticket 0011) habe ich die IDN-Naht, ihren
Adapter und einen Meldungs-Renderer in
`contexts/identity/application/shared/` gelegt, mit der Begruendung "das
brauchen alle Use Cases mit E-Mail-Eingabe". Es gab genau einen Use Case. Der
Nutzer hat es unmissverstaendlich zurueckgewiesen: *"wieso ist das shared? …
da ist nix zu sharen"* - und gleich die Regel mitgeliefert, wann es doch dorthin
darf. `register_user/abstractions/` und `register_user/adapters/` existierten
bereits; ich habe eine zweite, leere Struktur daneben gebaut. Der Meldungs-
Renderer, den ich als eigenes `shared`-Modul geplant hatte, ist beim Umbau auf
eine Funktion in `validators/` zusammengeschrumpft - er wurde nie von mehr als
einer Stelle gebraucht.

**How to apply:** Bevor ein Ordner `shared/`/`common/` oder ein Modul im
`shared_kernel` entsteht: **zwei konkrete, existierende Aufrufer benennen.**
Gelingt das nicht, gehoert der Baustein in den Slice, der ihn braucht. Das
Argument "die anderen werden das auch brauchen" ist eine Vorhersage, keine
Anforderung - und ein Umzug spaeter ist billig, waehrend eine falsch
positionierte Abstraktion jeden weiteren Slice praegt. Gilt genauso fuer
Protocols und Ergebnis-Unions, nicht nur fuer Code mit Logik. Verwandt:
[[referenzimplementierung-schlaegt-prosa]].
