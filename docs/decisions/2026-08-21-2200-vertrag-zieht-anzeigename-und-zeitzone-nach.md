# Der Vertrag zieht Anzeigename und Zeitzone nach

**Datum:** 2026-08-21, 22:00
**Anlass:** [#95](https://github.com/mbalzert1978/fit_back/issues/95) — die Referenz-Implementierung
von `POST /api/v1/identity/register`. Zwei Interaktionen des Identity-Pacts kollidieren mit
Invarianten aus [`docs/Draft/BACKEND.md`](../Draft/BACKEND.md) Abschnitt 1. Nach
[2026-08-21-1330](2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md) Punkt 1 gewinnt der
Vertrag, und die Invariante wird nachgezogen — hier ist beides aufgeschrieben.

## 1. `UserTimeZone` nimmt einen festen UTC-Versatz an

Die Interaktion „Registrierung mit einer Versatz-Zone" schickt `timeZoneId: "GMT+01:00"` und
erwartet darauf eine **201**. Gemessen gegen `zoneinfo.available_timezones()`: `GMT+01:00` → `False`,
`Europe/Berlin` → `True`, `Etc/GMT-1` → `True`. Die bisherige Prüfung hätte den Vertragswert
abgelehnt.

**Entschieden:** `UserTimeZone` kennt ab jetzt zwei Formen — eine bekannte IANA-Kennung oder einen
festen Versatz gegen UTC. Der Versatz wird auf **eine** Schreibweise normalisiert (`±HH:MM`), weil
`GMT+01:00`, `+0100` und `+01:00` sonst drei Werte für dieselbe Zone wären. Die Antwort des
Vertrags nennt für diesen Fall exakt `"+01:00"` und trägt dort keinen Matcher — die Normalisierung
ist damit nicht Geschmack, sondern Vorgabe.

Die IANA-Datenbank wird zuerst befragt: `Etc/GMT-1` ist eine Kennung und soll eine bleiben.

**Was das kostet:** Wer den Wert in eine `tzinfo` verwandelt, muss beide Formen behandeln —
`ZoneInfo` kennt den Versatz nicht, `datetime.timezone` kennt keine Sommerzeit. Das trifft die
Tagebuch-Auswertungen, sobald es sie gibt; für den Kalendertag selbst ist es folgenlos, den bestimmt
nach [2026-08-21-1330](2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md) Punkt 4 ohnehin
der Client.

`tzdata` bleibt Pflicht-Dependency: die IANA-Form ist der Normalfall geblieben.

## 2. `DisplayName` verlangt mindestens zwei Zeichen

Beide 422-Interaktionen schicken `displayName: "a"` und erwarten einen Eintrag unter
`errors.displayName`. Bisher galt 1–60 Zeichen; ein einzelnes Zeichen wäre durchgegangen und die
Antwort hätte den erwarteten Feldfehler nicht enthalten.

**Entschieden:** 2–60 Zeichen. `BACKEND.md` Abschnitt 1 ist entsprechend nachgezogen, samt der
Invariantenzeile („`DisplayName` nicht leer" → „mindestens 2 Zeichen").

Der zu kurze Name bekommt einen **eigenen** Fall (`DisplayNameTooShort`, Code
`display-name-too-short`) neben dem leeren (`DisplayNameIsEmpty`). Die Mindestlänge deckt den leeren
Namen zwar mit ab, aber „gar nichts eingegeben" und „zu wenig eingegeben" sind für den Aufrufer zwei
verschiedene Auskünfte, und nur die zweite kann eine Länge nennen. Die Textvorlagen stehen in beiden
Sprachen; der Wortlaut ist frei, der Vertrag typprüft ihn nur.

## Was dadurch ausgeschlossen wird

- Keine Rückfrage an den Consumer zu diesen beiden Werten — der Vertrag entscheidet (Punkt 6 der
  Vertrags-Entscheidung).
- Keine zweite Schreibweise desselben Versatzes im Bestand.
- Kein stilles Zusammenfassen von „leer" und „zu kurz" zu einem Fehlercode.
