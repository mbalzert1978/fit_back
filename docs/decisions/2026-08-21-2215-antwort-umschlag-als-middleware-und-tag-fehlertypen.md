# Der Antwort-Umschlag ist Middleware, und Fehlertypen sind `tag:`-URIs

**Datum:** 2026-08-21, 22:15
**Anlass:** [#95](https://github.com/mbalzert1978/fit_back/issues/95). Der Identity-Pact verlangt
für 2xx einen `{data, meta}`-Umschlag, für 4xx nacktes `application/problem+json` — und benennt
Fehlertypen unter `tag:nutritrack.app,2026:problems/<slug>` statt unter der bisherigen
Phantasie-URL `https://api.example/errors/<slug>`.

## 1. Der Umschlag kommt aus einer Middleware, nicht aus dem Router

`ResponseEnvelopeMiddleware` (`src/middleware/response_envelope.py`) legt `{data, meta}` um **jede**
erfolgreiche JSON-Antwort des Hosts und setzt dabei `X-Request-Id` und `Cache-Control: no-store`.
Sie gilt ab hier für den ganzen Host, nicht nur für Identity: der nächste Endpunkt bekommt den
Umschlag ohne eigene Zeile, und keiner kann ihn vergessen oder anders bauen. Der Health-Check
antwortet seitdem ebenfalls darin: `GET /api/v1/health` liefert `{"data": {"status": "healthy"},
"meta": …}` statt `{"status": "healthy"}`. Das ist eine **host-weite Formänderung**, keine
Identity-Änderung — eine externe Sonde, die `.status` liest, muss auf `.data.status` gezogen werden.

Die Anfrage-Kennung entsteht in der Middleware und wird **nicht** aus der Anfrage übernommen: ein
Wert vom Aufrufer wäre in Länge und Zeichenvorrat fremdbestimmt und landete ungeprüft im Log und im
Antwortkörper.

**Nur um 2xx.** Fehlerkörper sind RFC 7807 und im Vertrag nicht eingepackt; ein Umschlag darum wäre
ein zweites Fehlerformat neben dem einen, das der Consumer liest. `X-Request-Id` geht trotzdem an
jede Antwort — genau die fehlerhafte will man später im Log wiederfinden.

**Reihenfolge in der Kette:** Auffangpunkt für unbehandelte Ausnahmen außen, dann der Umschlag, dann
die Idempotenz. Was die Idempotenz-Middleware ablegt, ist damit der nackte Körper; eine wiederholte
Anfrage bekommt ihn mit ihrer *eigenen* `requestId` neu eingepackt statt mit der von gestern.

`meta.timestamp` kommt aus der injizierten `TimeProvider`, nicht aus `datetime.utcnow()` — dieselbe
Zeitquelle wie überall sonst.

## 2. Ein Fehlertyp ist ein Bezeichner, keine Adresse

`problem_type(slug)` in `src/api/problem_details.py` ist die **eine** Stelle, an der der Präfix
steht; Router, Exception-Handler und beide Middlewares rufen sie. Ein `tag:`-URI (RFC 4151)
verspricht nichts Abrufbares und bindet den Bezeichner nicht an einen Hostnamen, der sich ändern
kann. Der Wert steht ohne Matcher im Vertrag und ist damit bindend.

## 3. Validierungsfehler sind 422, nicht 400

Beide Wege — die strukturelle Prüfung von Pydantic und das Regelwerk des Slice — antworten jetzt mit
**422**. Der Körper war lesbares JSON, nur sein Inhalt hat die Regeln nicht bestanden (RFC 9110
Abschnitt 15.5.21). Der Vertrag nennt den Code ohne Matcher.

Damit fällt die frühere Festlegung „400 statt FastAPIs 422, damit der Aufrufer überall dasselbe
Format sieht": dasselbe Format bleibt, der Code wird der richtige.

## Was dadurch ausgeschlossen wird

- Kein Endpunkt baut `data`/`meta` selbst.
- Kein eingepackter Fehlerkörper.
- Kein `https://api.example/errors/...` mehr, und kein zweiter Ort, der Fehlertypen zusammensetzt.
- Kein 400 mehr für inhaltlich ungültige Eingaben.
