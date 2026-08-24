# Der Idempotenz-Replay wiederholt den Erstaufruf, statt ihn zu paraphrasieren

**Datum:** 2026-08-24, 18:00
**Anlass:** Der Replay-Zweig in `src/middleware/idempotency.py` antwortete fest mit
`JSONResponse(content=..., status_code=200)`. Eine wiederholte Registrierung bekam damit `200`
statt `201` und verlor `Location` und `Content-Language`, die der Router
(`src/api/identity/register_user_router.py`) an die `201` haengt.

## Entschieden

**Die Reservierung zeichnet die ganze Antwort auf, und der Replay gibt sie unveraendert wieder** —
Rumpf, Statuscode und die Kopfzeilen aus einer benannten Erlaubnisliste.

- Neue Spalten `response_status` (SMALLINT) und `response_headers` (TEXT, JSON-Objekt), beide
  nullable, Migration `shared_005`.
- `REPLAYED_HEADERS = {"location", "content-language"}` — eine **Erlaubnisliste**, keine
  Sperrliste. Blind alles zu speichern hiesse, `Content-Length` und `Date` des Erstaufrufs Tage
  spaeter erneut auszuliefern: beschreibende Kopfzeilen, die nur fuer die Antwort von damals
  galten. `X-Request-Id` und `Cache-Control` setzt der Umschlag ohnehin neu, fuer *diese* Anfrage.
- `NULL` in den neuen Spalten heisst „nicht aufgezeichnet"; solche Zeilen — alles, was vor
  `shared_005` entstand, und der Provider-State in `tests/contracts/idempotency_key.py` — fallen
  auf das alte Verhalten zurueck (`200`, keine Kopfzeilen). Keine Datenmigration noetig.

Der Grund ist der Sinn des Verfahrens selbst: der Aufrufer, dem die erste Antwort unterwegs
verloren ging, darf **nicht an der Antwort erkennen koennen**, dass er der zweite war. Ein Replay,
der denselben Rumpf unter einem anderen Statuscode und ohne `Location` ausliefert, zwingt jeden
Client zu zwei Auswertungspfaden fuer denselben Vorgang.

## Was das ueberschreibt

`docs/Draft/BACKEND.md` Abschnitt 0.3 (Zeile 44) und Zeile 587 schreiben woertlich vor: „Ein
bereits verarbeiteter Key liefert die ursprüngliche Antwort mit `200` statt `201`." Diese Regel
gilt nicht mehr — der Statuscode des Erstaufrufs wird wiederholt.

Das ist **kein** Vertragsbruch: der Pact
(`contracts/pacts/identity/nutritrack-app-nutritrack-identity.json`) prueft den Doppelaufruf mit
demselben Schluessel nicht; er kennt nur den Fall „Schluessel fuer eine *andere* Anfrage
wiederverwendet" (409, siehe [`2026-08-22-1500`](2026-08-22-1500-idempotency-key-wiederverwendung-ist-409.md)).
Wo der Vertrag schweigt, entscheidet die Invariante — die Umkehrung von
[`2026-08-21-1330`](2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md).

Damit wird auch ein Teil von
[`2026-08-06-1730`](2026-08-06-1730-idempotenz-reservieren-statt-nachtragen.md) korrigiert. Dort
wurde ein Design-Gate zurueckgewiesen, das genau diesen `200` aendern wollte — mit der Begruendung,
Abschnitt 0.3 schreibe ihn woertlich vor. Die Begruendung stimmte; die Beobachtung des Gates auch.
Was damals fehlte, war der zweite Teil des Befunds: nicht nur der Statuscode wich ab, sondern die
gesamte Antwort, inklusive der Kopfzeilen. Erst damit ist es kein Streit ueber eine Ziffer mehr,
sondern ueber die Frage, ob der Replay den Erstaufruf ueberhaupt wiederholt.

Der Rest von `2026-08-06-1730` bleibt unberuehrt: Reservieren-dann-arbeiten,
`ON CONFLICT DO NOTHING RETURNING`, der `request_hash`-Vergleich, die Freigabe der Reservierung
ohne wiederholbare Antwort.

## Was dadurch ausgeschlossen wird

- Kein fester Statuscode im Replay mehr.
- Kein blindes Speichern *aller* Antwort-Kopfzeilen — nur die benannten.
- Kein Umschlag um den gespeicherten Rumpf: `ResponseEnvelopeMiddleware` liegt ausserhalb der
  Idempotenz (`src/main.py`), abgelegt wird der nackte Koerper, und der Replay wird auf dem
  Rueckweg mit seiner *eigenen* `requestId` neu eingepackt. Ein Test belegt das.
