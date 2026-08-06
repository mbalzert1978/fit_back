# Zeitpunkte sind Unix-Sekunden, nicht `datetime` — und das schlaegt BACKEND.md §0.12

**Datum:** 2026-08-06, 13:40
**Anlass:** Review des Referenz-Slice `register_user` (Ticket
[0011](../issues/0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md), Stufe 1).

## Der Widerspruch, der aufgefallen ist

Zwei Vorgaben dieses Repos sagten fuer denselben Sachverhalt Verschiedenes:

- [`.rules/python/python-data-access.md`](../../.rules/python/python-data-access.md), Abschnitt
  „Zeitpunkte als Unix-Sekunden-Value-Object": Zeitpunkte werden als **Unix-Sekunden (`int`)** in
  einem Value Object gehalten, ausdruecklich **nicht** als rohes `datetime`.
- [`docs/Draft/BACKEND.md`](../Draft/BACKEND.md) §0.12: „Jeder Zeitstempel in Domaene, Persistenz
  und Transport ist `DateTimeOffset` (PostgreSQL `timestamptz`)."

Der erste Bau des Slice folgte stillschweigend BACKEND.md — nicht aus Abwaegung, sondern weil der
bereits gemergte `TimeProvider` (Ticket 0004) `datetime` liefert. Weder das Regel-Review noch das
Qualitaets-Review haben den Widerspruch aufgedeckt; eines hat ihn sogar ausdruecklich als
„kein Finding, betrifft Stufe 2" abgeraeumt, obwohl die Regel unbedingt gilt und die Domaene meint.

## Entscheidung

**Die Regel gewinnt.** Ein Zeitpunkt ist in Domaene und Persistenz ein `int` Unix-Sekunden,
gewrappt in `src/shared_kernel/timestamp.py::Timestamp`. Fuer den Python-Port dieses Projekts ist
**BACKEND.md §0.12 damit ueberschrieben**, soweit er `DateTimeOffset`/`timestamptz` fordert.

Begruendung des Nutzers, und sie traegt: ein `int` verhaelt sich in **jeder** Engine gleich —
PostgreSQL `bigint`, SQLite `INTEGER` — waehrend `timestamptz` ein PostgreSQL-Spezifikum ist. Der
Zeittyp soll die Wahl der Datenbank nicht praejudizieren. Dazu kommt, was die Regel selbst nennt:
keine Zeitzonen- und keine Serialisierungs-Mehrdeutigkeit am Persistenzrand.

## Was daraus folgt

- **Persistenz** (Stufe 2): die Spalte ist `bigint`, nicht `timestamptz`.
- **Transport**: unveraendert ISO-8601-UTC, wie in den API-Contracts von BACKEND.md §1 ff.
  gezeigt. Die Umrechnung passiert in der HTTP-Schicht ueber `Timestamp.to_datetime()` — „nur am
  Rand, wenn ueberhaupt eine Anzeige noetig ist" (Regeltext). Application-DTOs tragen den rohen
  `int` und benennen ihn entsprechend (`registered_at_unix`).
- **`TimeProvider`** hat jetzt zwei Zugriffe: `now() -> Timestamp` ist der domaenenseitige Weg,
  `utc_now() -> datetime` bleibt die rohe Systemablesung fuer den Rand. Bestehende Aufrufer aus
  M0 bleiben unveraendert lauffaehig.
- **Kalendertage** sind davon **nicht** betroffen. BACKEND.md §0.4 und §0.12 definieren den
  Tagebuch-Tag als reinen Kalendertag in der Zeitzone des Nutzers; er bekommt in M4 ein eigenes
  Value Object `DiaryDate` und ist kein Zeitpunkt.
- **`UserTimeZone` bleibt** und wird von dieser Entscheidung nicht ueberfluessig. Die Zeitzone
  kodiert keinen Zeitpunkt — sie beantwortet, *welcher Kalendertag* ein Zeitpunkt fuer diesen
  Nutzer war. Ohne sie ist der Diary-Context nicht umsetzbar.

## Ueberpruefbar gemacht

`tests/test_architecture_datetime.py` verbietet bereits `datetime.now()`/`utcnow()` ausserhalb des
`TimeProvider`. Das ist notwendig, aber nicht hinreichend: es faengt nicht ab, dass ein Aggregat
einen `datetime` **haelt**. Ein Architekturtest dafuer fehlt noch — er wird beim zweiten Slice
nachgezogen, wenn absehbar ist, welche Ausnahmen der Rand wirklich braucht.
