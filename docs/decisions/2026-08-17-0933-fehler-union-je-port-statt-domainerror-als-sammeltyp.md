# Eine Fehler-Union je Port statt `DomainError` als Sammeltyp

**Datum:** 2026-08-17, 09:33
**Anlass:** Stufe 4 von Ticket [#51](https://github.com/mbalzert1978/fit_back/issues/51) —
Pipeline-Abstraktion im Referenz-Slice `register_user`.

## Was entschieden wurde

Jeder Domain-Port, jede `parse`-Factory und jede Domaenen-Regel traegt in `Result[T, E]` die
Union ihrer **eigenen erwarteten Ausgaenge**:

- `UserRegistryError = EmailAlreadyRegistered` (`domain/ports/user_registry.py`)
- `IdnEncoderError = UnencodableDomainLabel` (`domain/ports/idn_encoder.py`)
- `EmailError`, `PasswordError`, … wie bisher fuer die Value Objects

Damit ist die frueher in `domain/errors.py` festgehaltene Zusage — „alle Domain-Ports sprechen
`Result[T, DomainError]` mit **diesem** `E`" — aufgehoben.

`DomainError` bleibt bestehen, aber mit einer anderen Aufgabe: es ist die **Volkszaehlung** aller
Fehlerfaelle des Context, gegen die die Fehlercode- und i18n-Drift-Pruefungen zaehlen. Dass es
diese Rolle wirklich hat und nicht nur herumliegt, haelt
`tests/contexts/identity/test_published_error_vocabulary.py::test_kein_fehlerfall_faellt_zwischen_die_mengen`
fest.

## Warum

Der Sammeltyp verspricht an jeder Naht alles, was es im Context gibt. Wer ihn faltet, muss jeden
Fall behandeln, obwohl nur einer eintreten kann. Im Response-Mapper des Referenz-Slice waren das
zweiundzwanzig Arme fuer **einen** erreichbaren Ausgang; die uebrigen einundzwanzig waren entweder
eine zweite Abschrift der Code-und-Parameter-Tabelle aus `validators/register_user_rules.py` oder
einundzwanzigmal dasselbe „kann nicht sein".

Der Preis war nicht nur Laenge. Der abschliessende `assert_never` — laut
[`2026-08-07-1120`](./2026-08-07-1120-jeder-match-endet-mit-assert-never.md) der Wachposten hinter
jedem `match` — konnte „neu dazugekommen" nicht mehr von „gibt es laengst, hat nur niemand
angefasst" unterscheiden. Ein Wachposten hinter einundzwanzig Unmoeglichkeiten bewacht nichts.

Zweitens war der Sammeltyp an einer Stelle schlicht unwahr: `email.py` reicht das Ergebnis von
`IdnEncoder.to_ascii` als `Result[str, EmailError]` weiter, also durch eine Union, in der die
meisten `DomainError`-Faelle gar nicht vorkommen. Mit der schmalen Port-Union stimmt die
Annotation wieder.

## Was dadurch ersetzt wird

Zwei Punkte der Review-Checkliste in
[`.rules/python/python-feature-slices.md`](../../.rules/python/python-feature-slices.md) sagten
bislang das Gegenteil und sind mitgezogen:

- „der `Result`-Fehlertyp ist context-eigen, nicht use-case-eigen" — der Zusatz ist gestrichen.
- „Domain-Ports … geben durchgehend `Result[T, E]` mit **demselben einen, flachen** feature-eigenen
  Fehlertyp zurueck" — ersetzt durch die eigene, schmale Union je Operation.

Der Abschnitt „Die Domaene spricht durchgehend `Result[T, E]`" ist entsprechend neu gefasst,
inklusive Do/Don't.

## Was ausdruecklich nicht gilt

Eine Port-Union waechst mit den erwarteten Ausgaengen ihres Adapters — **nicht auf Verdacht**.
`UserRegistryError` bekommt heute keinen Fall `DatabaseUnreachable`, weil kein Adapter ihn
liefert; ein solcher Arm waere genau die Unerreichbarkeit, die hier abgeschafft wird. Sobald ein
Adapter einen erwarteten IO-Ausgang als Wert melden soll, gehoert er dorthin (als Fall im `Result`,
nicht als Exception). Unerwartetes bubbelt weiterhin hoch.
