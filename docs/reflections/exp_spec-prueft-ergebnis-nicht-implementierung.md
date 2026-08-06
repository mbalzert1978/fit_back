---
schema_version: 1
name: spec-prueft-ergebnis-nicht-implementierung
description: Viele Eingabefaelle rechtfertigen keine tiefere Testebene - Tabellen laufen durch die Test-API, und fremde Bibliotheken werden nie mitgetestet
type: feedback
frequency: 1
last_triggered: 2026-08-06
decay_eligible: true
---

Eine Tabelle mit vielen Eingabefaellen ist **kein** Grund, unterhalb der Test-API
zu testen. Die Faelle sind Eingaben, keine neue Testebene. Und was hinter einem
Port eine externe Bibliothek entscheidet, wird gar nicht spezifiziert.

**Why:** Beim Bau des Referenz-Slice (Ticket 0011) landeten 42 E-Mail-Faelle aus
dem Review als Domain-Unit-Test gegen `Email.parse(candidate, idn)`. Zwei
Beobachtungen entlarvten das:

1. Die Signatur von `Email.parse` aenderte sich in **derselben Sitzung zweimal**
   (IDN-Port, `DomainError` statt `str`) - der Test musste beide Male mit. Die
   Test-API-Specs daneben ueberlebten beide Umbauten unveraendert. Ein Test, der
   bei jeder internen Umstellung mitwandert, sichert nichts ab; er dokumentiert
   den Ist-Zustand.
2. Um den einen IDN-Fall zu pruefen, zog der Test die echte `idna`-Bibliothek
   **plus** den Infrastruktur-Adapter herein. Damit wurde fremder Code getestet:
   bricht `idna` in einer neuen Version, bricht unser Test, ohne dass wir etwas
   ueber unsere Domaene gelernt haetten. Der Nutzer brachte es auf den Punkt -
   man testet auch nicht vorab, ob `open()` Dateien oeffnen kann.

Der Testimport von `infrastructure/` war das sichtbare Warnsignal: ein Spec, der
Infrastruktur braucht, um eine Domaenenregel zu pruefen, sitzt auf der falschen
Ebene.

**How to apply:** Vor jedem Test unterhalb der Test-API zwei Fragen stellen.
*Ist das Verhalten ueber einen Use Case ueberhaupt erreichbar?* Wenn ja, gehoert
der Spec dorthin - auch wenn er ueber die Test-API umstaendlicher zu formulieren
ist und die Aufloesung sinkt („ungueltig" statt „welche Regel gefeuert hat"; das
ist Implementierung und darf unsichtbar bleiben). *Entscheidet den Fall eine
externe Bibliothek?* Dann wird er gar nicht spezifiziert, und der Fake hinter
der Naht sagt ehrlich, dass er es nicht kann, statt das Verhalten nachzubauen -
ein nachgebauter Fake prueft die Spezifikation gegen sich selbst.

Festgehalten in `.rules/python/python-feature-slices.md`, Abschnitte „Ein Spec
prueft das Ergebnis, nicht den Weg dorthin" und „Fremde Bibliotheken werden
nicht mitgetestet". Verwandt: [[referenzimplementierung-schlaegt-prosa]],
[[brief-traegt-die-form-nicht-die-loesung]].
