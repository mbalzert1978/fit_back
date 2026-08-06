---
schema_version: 1
name: infrastruktur-erfuellt-naht-adapter-implementiert-port
description: Infrastruktur implementiert NIE direkt einen Domain-Port - sie erfuellt nur die public Naht (Primitive rein, eigene Union raus), und ein Adapter uebersetzt das in Result[T, DomainError]
type: feedback
frequency: 2
last_triggered: 2026-08-06
decay_eligible: true
---

Zwischen Bibliothek und Domaene liegen **immer zwei** Stufen, nie eine:

1. Die **Naht** (`abstractions/`) - vom Use Case formuliert, nur Primitive,
   eigene Tagged Union als Ergebnis. Die Infrastruktur erfuellt genau diese und
   kennt die Domaene nicht.
2. Der **Adapter** (`adapters/`) - implementiert den Domain-Port und uebersetzt
   die Naht-Union in `Result[T, DomainError]`.

Der Domain-Port spricht dabei **denselben flachen Fehlertyp des Contexts**, nie
einen `str` - er ist ein Domaenenbaustein wie jeder andere.

**Why:** Beim Einbau der IDN-Bibliothek habe ich die Abkuerzung genommen und in
`shared_infrastructure/idn/` eine Klasse geschrieben, die den Domain-Port
`IdnEncoder` direkt implementiert. Der Nutzer: *"nein infra darf nicht direkt
den port implementieren das läuft immer durch adapter layer"* - und kurz zuvor:
*"bitte passenden domainerror einführen nicht str"*. Beide Punkte standen
bereits in der Review-Checkliste von `python-feature-slices.md`; ich habe sie
verletzt, weil die neue Abhaengigkeit spaet dazukam und ich sie "nur schnell"
anbinden wollte. Die Folgekosten waren keine: die Umstellung zog die gesamte
Email-Pruefkette von Prosa-Strings auf 14 typisierte Fehlerfaelle - eine
Verbesserung, die ohne die Korrektur nie passiert waere.

**How to apply:** Sobald ein Slice eine **neue externe Abhaengigkeit** bekommt
(Bibliothek, Dienst, Dateisystem), die drei Fragen stellen, **bevor** Code
entsteht: Wo ist die Naht, und traegt sie nur Primitive? Wo ist der Adapter?
Spricht der Domain-Port den `DomainError` des Contexts? Ein Infrastruktur-Modul,
das einen Typ aus `domain/` importiert, ist das sichtbare Warnsignal - es darf
hoechstens die Naht-Typen aus `application/<use_case>/abstractions/` kennen.
Verwandt: [[maschinelle-absicherung-statt-review-regel]] (der
import-linter-Contract faengt die Richtung, nicht die fehlende Zwischenstufe).
