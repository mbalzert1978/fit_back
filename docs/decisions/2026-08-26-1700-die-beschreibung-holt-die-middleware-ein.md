# Die veröffentlichte Beschreibung holt die Middleware ein

**Entschieden am 2026-08-26, 17:00.**

## Was entschieden wurde

Das OpenAPI-Dokument dieser API wird **nach** seiner Erzeugung ergänzt, an einer Stelle für den
ganzen Host: [`src/api/openapi.py`](../../src/api/openapi.py), aufgerufen aus
[`src/main.py`](../../src/main.py), nachdem alle Router eingehängt sind.

Der Nachtrag trägt vier Dinge ein:

1. Jede erfolgreiche JSON-Antwort wird als `{data, meta}` beschrieben — die Form, die
   `ResponseEnvelopeMiddleware` ihr gibt. Der `meta`-Block bekommt mit `ResponseMeta` ein eigenes
   Schema.
2. Jeder Fehlerkörper wird von `application/json` auf `application/problem+json` umgehängt.
   Umgehängt, nicht ergänzt: unter `application/json` liefert diese API keinen Fehlerkörper aus.
3. Jede Antwort nennt `X-Request-Id` und `Cache-Control`.
4. `info.version` ist `API_VERSION` und damit dieselbe Angabe wie `/api/v1` und `meta.apiVersion`.

> **Nachgetragen am 2026-08-27:** Punkt 4 stimmte nicht. Der Nachtrag fasste `info.version` nie an —
> gesetzt war sie allein an `FastAPI(version=...)` in `src/main.py`. Er trägt sie jetzt selbst ein.
> Die Konstante heißt nicht mehr `API_VERSION`, sondern `DEFAULT_API_VERSION` in
> [`src/settings.py`](../../src/settings.py) und ist über `API_VERSION` in der Umgebung
> überschreibbar. Siehe
> [2026-08-27-1500](2026-08-27-1500-review-durchgang-fabrik-sperre-und-api-version.md), Abschnitt 5.

Was nur zu **einer** Route gehört, steht weiterhin in deren `responses` — `Location` und
`Content-Language` der 201 von `POST /api/v1/identity/register` etwa.

## Warum

FastAPI beschreibt, was ein Endpunkt **zurückgibt**. Was der Aufrufer empfängt, entsteht erst
danach in der Middleware-Kette. Beides lief auseinander, und zwar still: das Dokument nannte
`RegisterUserResponse` an der Wurzel, die Leitung lieferte `data` und `meta`. Ein aus der
Beschreibung erzeugter Client hätte an der falschen Stelle gesucht.

Am ganzen Dokument und nicht je Route, weil auch die Middleware am ganzen Host greift. Eine neue
Route ist damit von selbst richtig beschrieben, und niemand kann den Nachtrag an einer Stelle
vergessen. Die umgekehrte Aufteilung — jede Route beschreibt ihren eigenen Umschlag — wäre dieselbe
Aussage an so vielen Stellen, wie es Routen gibt.

## Was dadurch ausgeschlossen ist

- **`app.openapi` ersetzen.** Der in der FastAPI-Dokumentation gezeigte Weg. Eine gewöhnliche
  Funktion ist an dieser Stelle keine Methode, und `ty` lehnt die Zuweisung ab; das Repo führt
  seit dem [Typprüfer-Gate](2026-08-25-1500-typechecker-ty.md) keine Baseline und kein
  `type: ignore` dafür. Stattdessen wird `app.openapi_schema` gefüllt — derselbe
  Zwischenspeicher, den FastAPI selbst benutzt.
- **`get_openapi(...)` selbst aufrufen.** Müsste jedes Feld der App von Hand weiterreichen und
  ginge still schief, sobald eines dazukommt.
- **Den Umschlag als `response_model` je Route.** Der Endpunkt gibt den nackten Körper zurück;
  ein `response_model`, das den Umschlag nennt, würde ihn gegen eine Form prüfen, die er nicht
  hat.

## Was daran nicht selbsttragend ist

`ResponseMeta` wird nie instanziiert — es beschreibt einen Block, den die Middleware selbst
schreibt. Ohne Prüfung könnte es ein Feld nennen, das es nicht gibt.
`tests/api/test_openapi_description.py` hält beide Seiten aneinander.
