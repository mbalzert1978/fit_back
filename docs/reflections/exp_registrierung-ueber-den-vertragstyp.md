---
schema_version: 1
name: registrierung-ueber-den-vertragstyp
description: An einer Registry wird ueber den Vertragstyp registriert, nie ueber einen String - der Wire-Name lebt einmal als Konstante auf dem Vertrag selbst
type: feedback
frequency: 1
last_triggered: 2026-08-06
decay_eligible: true
---

Eine Registry nimmt den **Typ** entgegen, nicht seinen Namen:
`registry.register(UserRegistered, handler)`, nicht
`registry.register("UserRegistered", handler)`. Der Name auf der Leitung steht
genau einmal, als `EVENT_TYPE: ClassVar[str]` auf dem Vertrag - und als
**Konstante**, nicht als `__name__`: umbenannte Klassen duerfen bereits
geschriebene Zeilen nicht verwaisen lassen.

**Why:** Der erste Entwurf der `EventRegistry` nahm einen String. Der Nutzer:
*„nicht mit string als event sondern nimm was typisiertes ... in unserem Fall
der public part des events waere mir am liebsten."* Mit dem Typ kann sich ein
Tippfehler nicht mehr als stiller Nicht-Treffer tarnen, die Registrierung findet
ihren Vertrag ueber „Definition anzeigen", und der Zusammenhang zwischen
Erzeuger und Verbraucher wird im Werkzeug sichtbar statt nur im Kopf. Genau
dieser Gedanke hat den `contracts/`-Ordner erzwungen: der veroeffentlichte
Vertrag ist das, was beide Seiten teilen duerfen - nicht das Domaenen-Event.

**How to apply:** Ueberall, wo etwas unter einem Schluessel abgelegt und spaeter
wiedergefunden wird (Event-Handler, Serialisierer, Kommando-Dispatch, Plugins),
zuerst fragen, ob es statt eines Strings einen Typ gibt, der denselben Dienst
tut. Wenn ja: die Signatur generisch ueber diesen Typ binden
(`def register[T: DomainEvent](self, event: type[T], ...)`) und den String im
Inneren aus einem `ClassVar` ziehen. Bleibt ein String noetig, gehoert er auf
den Vertrag, nicht an die Aufrufstelle.
