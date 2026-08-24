# `any_of` (OR) ist gebaut — der erste Fall war die Zeitzone

**Datum:** 2026-08-24, 15:00
**Status:** entschieden — gebaut
**Loest ab:** die offene Frage aus
[`2026-08-07-1331-or-und-conditional-rule-erst-beim-ersten-fall.md`](./2026-08-07-1331-or-und-conditional-rule-erst-beim-ersten-fall.md)

## Der Anlass

`UserTimeZone.parse` war die letzte `parse`-Methode im Identity-Context, die ihre Fachlogik noch
als `if`-Kette trug. Der Grund war kein Versehen: Eine Zeitzone ist eine IANA-Kennung **oder** ein
fester UTC-Versatz — ein ODER, und `chain` bindet. Der Kombinator dafuer war bewusst nicht gebaut,
bis der erste echte Fall auftaucht. Das ist dieser Fall.

## Die eine offene Frage — und ihre Antwort

Die Vorentscheidung hat alles geklaert bis auf: **welchen Fehler meldet ODER, wenn alle Zweige
scheitern?** Drei Antworten standen zur Wahl (alle sammeln / den ersten / einen eigenen Fall).

**Gewaehlt: der eigene Fall — aber der Kombinator liefert ihn nicht.** `any_of` gibt den Fehler
des **letzten** Zweigs zurueck und erklaert das ausdruecklich zur Nicht-Aussage. Den ehrlichen
Fall setzt der Aufrufer per `map_err`:

```python
_RULES: ResultRule[str, UserTimeZoneError] = any_of(is_known_time_zone_id, is_fixed_utc_offset)

return _RULES(raw.strip()).map_err(lambda _: UserTimeZoneUnknown(raw)).map(cls)
```

Damit entfaellt der `sonst`-Parameter, den die Vorentscheidung als plausible Signatur skizziert
hatte. Der Grund: `map_err` gibt es bereits und leistet genau dasselbe, nur ohne dass der
Kombinator einen Fehlerfall entgegennehmen und durchreichen muss. Eine Zwischenschicht weniger —
konsistent mit der Review-Checkliste in `.rules/python/python-rule-pattern.md`
(„Die Fallunterscheidung steht in der Regel, nicht in einem generischen Helfer mit
Konverter-Callback").

Der zweite offene Punkt der Vorentscheidung — ODER ueber Felder **verschiedener** Namen und das
fehlende `field` — stellt sich hier nicht: beide Zweige beantworten dieselbe Frage ueber dasselbe
Feld. Er bleibt offen, bis ein Fall ihn stellt.

## Wie er gebaut ist

- **`Result.or_else`** in `shared_kernel/result.py` — das Gegenstueck zu `bind`: `Ok` ignoriert die
  Alternative, `Err` fuehrt sie aus. Damit kommt `any_of` ohne `isinstance` und ohne `match` aus,
  genau wie `chain` ohne beides auskommt.
- **`any_of(first, *rest)`** in `shared_kernel/validation.py`. Die erste Regel steht als eigener
  Parameter, weil ODER **kein neutrales Element** hat: `all_of()` darf mit null Regeln „alles
  gueltig" bedeuten, `any_of()` haette mit null Zweigen keinen Fehler zu melden.
- Die **Reihenfolge ist fachlich**, nicht beliebig: `Etc/GMT-1` ist eine IANA-Kennung und kein
  Versatz, also steht `is_known_time_zone_id` vorn.
- Belegt durch `tests/contexts/test_any_of.py`, insbesondere: nach einem Treffer laeuft kein
  weiterer Zweig.

## Was dadurch ausgeschlossen bleibt

**Conditional Rule** bleibt abgelehnt — daran aendert dieser Fall nichts. Die Absage in der
Vorentscheidung ist keine Terminfrage, sondern begruendet: eine Regel ist hier eine Funktion und
darf selbst verzweigen.

## Folgen

- `.rules/python/python-rule-pattern.md` wird nachgezogen: der Abschnitt, der ODER als „bewusst
  nicht gebaut" fuehrt, beschreibt es jetzt als dritten Kombinator neben `all_of` und `chain`.
- `docs/reference/rule-engine-pattern.md` verweist weiterhin auf die Vorentscheidung; deren
  Analyse bleibt gueltig, nur die offene Frage ist beantwortet.

## Nachtrag: `ParseRule` und `not_blank` als erste Regel

Zwei Korrekturen aus derselben Sitzung, die zum selben Bild gehoeren:

**`ParseRule[TIn, TOut, E]`** — eine Pruefung, die den Wert dabei in seine gueltige Form
ueberfuehrt (`str -> UUID` in `UserId`, `str -> Locale` in `Locale`), ist **trotzdem eine Regel**
und wird wie jede andere als benannte Funktion herausgezogen und als `_RULE` deklariert. Sie ist
nur nicht verkettbar: `chain`/`any_of` setzen gleiche Ein- und Ausgangsform voraus. `ResultRule`
ist seither als der wertformerhaltende Sonderfall `ParseRule[T, T, E]` definiert — die Beziehung
steht damit im Typ und nicht in einem Kommentar. Verkettet wird eine `ParseRule` per `.bind`
(`parse_locale`: `is_not_blank(raw).bind(_RULE)`).

Ein eigener Kombinator fuer diese Verkettung wurde **nicht** gebaut: es gaebe genau einen
Aufrufer, und `.bind` leistet dort dasselbe in derselben Zeilenzahl.

**`not_blank` als erste Regel statt `raw.strip()` daneben.** `UserTimeZone.parse` und
`parse_locale` trimmten den Rohwert von Hand, bevor die Regeln liefen. Das ist dieselbe
Vermischung, die das Muster ueberhaupt aufloesen soll: eine Vorbereitung neben den Regeln, die
niemand als Regel sieht und die jede folgende Pruefung stillschweigend voraussetzt. Beide fuehren
jetzt `not_blank` als erste Regel ihrer Kette — es trimmt und urteilt in einem, und die folgenden
Regeln sehen bereits den getrimmten Wert.
