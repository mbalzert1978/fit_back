# Gemeldet wird erst, wenn Konto und Token stehen

## Was entschieden wurde

Die Meldung `UserRegistered` ist der **letzte** Schritt des Use Case. In der Kette des Handlers
wandert `inspect_async(self._announce)` hinter `map_async(self._with_credentials)`:

```python
.bind_async(self._registry.add)
.map_async(self._with_credentials)
.inspect_async(self._announce)
```

`_announce` bekommt dadurch die fertige `Registration` statt des nackten `User`.

## Warum die alte Reihenfolge falsch war

Die Meldung stand zwischen Aufnahme und Ausstellung. Sie behauptete damit einen Zustand, den es
noch nicht gab: „ein Nutzer ist registriert", während der Refresh-Token noch nicht abgelegt war.
Schlug die Ablage fehl, war die Meldung bereits geschrieben.

Der Fake zeigte genau das: `InMemoryEventLog` hielt das Ereignis fest, obwohl der Vorgang danach
abbrach. Belegt wird die neue Reihenfolge jetzt vom Spec
`test_wer_keinen_token_ablegen_konnte_wird_auch_nicht_gemeldet` — über
`RegisterUserTestApi.with_unavailable_token_store`.

## Was sich in der Produktion **nicht** ändert

Nichts, und das ist wichtig für das Verständnis der Änderung. Die Outbox schreibt die Ereigniszeile
in dieselbe Transaktion wie Nutzer und Token, und `pg_notify` stellt erst beim Commit zu
([Die Outbox ist ein Mechanismus, keine Naht](2026-08-06-1120-outbox-mechanismus-statt-naht.md)).
Ein Abbruch nahm die Meldung schon vorher mit zurück; nach außen war nie etwas sichtbar, was nicht
auch bestand.

Die Reihenfolge zu ändern kostet nichts und räumt trotzdem etwas auf: der Ablauf sagt jetzt, was er
meint, und hängt nicht mehr an einer Eigenschaft des Zustellwegs. Wer den Handler liest, muss die
Outbox nicht kennen, um ihn richtig zu finden — und ein späterer Zustellweg ohne diese Eigenschaft
bräche den Slice nicht.

## Was ausgeschlossen wird

Ein `bind_async` mit eigenem Fehlerfall für die Ausstellung wurde nicht eingeführt. Ein
fehlschlagender Token-Speicher bleibt ein Betriebsfall, kein fachlicher Ausgang — die Begründung
steht am Port `SessionIssuer` und ändert sich hierdurch nicht.
