# „Gar nichts angegeben" ist ein eigener Fehlerfall — auch bei Sprache und Zeitzone

**Datum:** 2026-08-24, 17:30
**Status:** entschieden — umgesetzt

## Der Anlass

Seit `not_blank` als erste Regel jeder Textkette steht
([`2026-08-24-1500-…`](./2026-08-24-1500-any-of-gebaut-fuer-die-zeitzone.md)), ist der leere Wert
eine eigene, benannte Regel. Ihr Fehler war es nicht: `Locale` und `UserTimeZone` meldeten dafuer
denselben Fall wie fuer einen inhaltlich falschen Wert. Herausgekommen waeren Meldungen wie „Die
Sprache '   ' wird nicht unterstuetzt" — eine Auskunft, die auf nichts zeigt.

## Die Entscheidung

Zwei neue Faelle mit eigenem Code und eigenen Textvorlagen (`de-DE`, `en-US`):

- `LocaleIsEmpty` — `locale-is-empty`
- `UserTimeZoneIsEmpty` — `user-time-zone-is-empty`

Beide tragen **keine** `candidate`-Nutzlast: es gibt keinen Wert zu nennen. Das ist dieselbe
Trennung, die `DisplayNameIsEmpty` von `DisplayNameTooShort` scheidet — sie war dort schon
begruendet und wird hier nur nachgezogen.

## Was **nicht** aufgeteilt wurde — und warum

Die beiden ODER-Zweige der Zeitzone (`is_known_time_zone_id`, `is_fixed_utc_offset`) haben
**keinen** je eigenen Fall bekommen, obwohl sie je einen melden koennten. Grund ist die
Vorentscheidung zu `any_of`: welcher Zweig zuletzt scheiterte, ist kein Befund. `+25:00` ist weder
Kennung noch Versatz; „keine IANA-Kennung" waere eine willkuerlich herausgegriffene Haelfte, beide
Meldungen zusammen waeren ein Widerspruch — der Aufrufer musste ja nur **eines** von beidem
liefern. Die zusammengesetzte Regel `has_a_known_form` traegt deshalb den einen Fall, der stimmt.

Ebenso wenig wurde ein Fall „Versatz ausserhalb des zulaessigen Bereichs" eingefuehrt. Ihn zu
erkennen hiesse, die ISO-8601-Auslegung neben `strptime("%z")` ein zweites Mal zu schreiben — und
die Begruendung, es *nicht* selbst zu parsen, steht in `_normalized_offset`.

## Der Nebenbefund, der teurer war als die Entscheidung

`register_user_rules.py` matchte auf die Fehler-Unions von Sprache und Zeitzone mit `assert_never`
als letztem Zweig. Ein neuer Fall in der Union heisst dort: **Laufzeitabbruch**, nicht Feldfehler —
und kein Test deckte einen reinen Leerraum-Wert in diesen beiden Feldern ab. Beide Zweige sind
ergaenzt, und `specs/register_user/test_register_user.py` haelt sie jetzt fest.

Die Lehre ist keine neue: `assert_never` ist genau dann wertvoll, wenn eine Union waechst — aber
er schuetzt nur den Typcheck, nicht den Testlauf. **Wer eine veroeffentlichte Fehler-Union
erweitert, sucht zuerst ihre `match`-Stellen und schreibt den Test dazu, bevor er den Fall baut.**
