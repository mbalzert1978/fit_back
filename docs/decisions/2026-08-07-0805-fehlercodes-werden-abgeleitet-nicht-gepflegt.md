# Die Menge der Fehlercodes wird aus den Slices abgeleitet, nicht danebengepflegt

**Datum:** 2026-08-07, 08:05

## Problem

Mit Ticket 0008 gibt es Fehlercodes im Code und Vorlagen unter denselben Codes in
`src/api/resources/*.json`. Das sind **zwei Listen**, die von Hand synchron gehalten werden — und
zwei solche Listen driften zuverlaessig auseinander.

Der erste Entwurf prueft beim Start nur, ob die **beiden Sprachdateien untereinander** dieselbe
Code-Menge haben. Das faengt eine vergessene Uebersetzung, aber nicht den Fall, um den es
eigentlich geht: ein neuer Slice bringt morgen neue Fehlerfaelle mit, und in **keiner** der Dateien
steht eine Vorlage dafuer. Die Anwendung startet froehlich und faellt erst um, wenn ein Nutzer
genau diesen Fehler ausloest — mit `AssertionError` und HTTP 500 fuer eine Eingabe, die eine 400
verdient haette.

Ebenso ungeprueft: ob die Platzhalter einer Vorlage (`{maximum}`) zu der Nutzlast passen, die der
Fehlerfall tatsaechlich traegt. Auch das schlaegt erst im Betrieb zu, als `KeyError` in `format`.

## Entscheidung

**Die erwartete Code-Menge wird aus den Fehler-Unions der Slices abgeleitet und beim Start gegen
die Resource-Files geprueft. Ein Drift laesst die Anwendung laut scheitern.**

Nicht: eine dritte Liste pflegen, die die beiden anderen vergleicht. Sondern: es gibt **eine**
Wahrheit, und die liegt dort, wo die Fehler entstehen.

Drei Bausteine:

1. **Der Code gehoert auf den Fehlerfall.** Jeder Fall der Union traegt seinen Code selbst.
   Ausdruecklich **nicht** aus dem Klassennamen abgeleitet: der Code ist veroeffentlichter
   API-Vertrag, eine Umbenennung der Klasse darf ihn nicht still aendern.

2. **Der Zusammenbau zaehlt auf.** Er ist die einzige Stelle, die alle Slices kennt — er wired sie.
   Er reicht die Unions in den Ressourcen-Aufbau hinein (passend zu
   [`…-0750-ressourcen-per-dependency-injection-statt-modulglobal.md`](2026-08-07-0750-ressourcen-per-dependency-injection-statt-modulglobal.md)).
   **Kein Registry mit Selbstregistrierung beim Import**: ein Slice, der nicht importiert wurde,
   fehlte dort still — die Pruefung wuerde gruen melden, was sie gar nicht gesehen hat
   ([`exp_gruenes-gate-ohne-scope-angabe.md`](../reflections/exp_gruenes-gate-ohne-scope-angabe.md)).
   Ein neuer Slice kostet eine Zeile an derselben Stelle, an der ohnehin sein Router registriert
   wird.

3. **Der Abgleich ist symmetrisch und prueft auch die Platzhalter.**
   - Code ohne Vorlage → Startfehler.
   - Vorlage ohne Code → **ebenfalls** Startfehler; Karteileichen sind die andere Haelfte des
     Drifts.
   - Verlangt eine Vorlage einen Platzhalter, den die Nutzlast des Falls nicht traegt → Startfehler.
     Die Nutzlast ist ueber `dataclasses.fields` lesbar, die Platzhalter ueber
     `string.Formatter().parse`.

Dieselbe Funktion, die beim Start prueft, ist als Test verwendbar — damit faellt der Drift schon in
CI auf, und die Startpruefung bleibt das Netz fuer den Fall, dass jemand nur eine JSON-Datei
anfasst.

## Folgen

- Der `AssertionError` in `translate` bleibt — aber er beruft sich dann auf eine Garantie, die
  wirklich existiert und maschinell durchgesetzt wird, statt auf eine bloss behauptete. Damit ist er
  im Sinne von `.rules/python/python-error-handling.md` korrekt: ein Fehlschlag dort ist ein
  Programmierfehler, kein erwarteter Ausgang.
- Kuenftige Slices erben die Pruefung, ohne etwas dafuer zu tun: sobald ihre Fehler-Union im
  Zusammenbau auftaucht, sind ihre Codes Teil der erwarteten Menge.
- Verworfene Alternativen: ein `Enum` aller Codes (waere die dritte Liste statt der ersten); ein
  Import-Zeit-Registry (siehe oben); Degradieren auf den Code als Anzeigetext (macht den Defekt
  leise — ausdruecklich nicht gewollt).
