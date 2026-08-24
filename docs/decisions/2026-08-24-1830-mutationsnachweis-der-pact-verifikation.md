# Mutationsnachweis: Was die Pact-Verifikation wirklich absichert

Das Acceptance-Kriterium aus [#95](https://github.com/mbalzert1978/fit_back/issues/95) verlangt
„Ein Bruch an einer der Interaktionen macht `./make.ps1 ci` rot — belegt, nicht behauptet".
Behauptet war es bis hierher; belegt ist es jetzt. Entschieden wurde: der Beleg wird als
**Mutationsexperiment** geführt — je ein einzelner, bewusst eingebauter Bruch im Produktionscode,
danach die Verifikation, danach sofortiges Zurücknehmen. Kein Test wurde dafür angefasst.

Gefahren wurde `uv run pytest tests/contracts/ -q` (statt `./make.ps1 ci`, weil in dieser
Umgebung kein `pwsh` vorliegt); der Verifier-Teil ist derselbe. Ausgangslage und Endstand:
`336 passed` bei `uv run pytest -q`.

Der Verifier läuft heute gegen **acht** Register-Interaktionen, nicht mehr gegen die fünf, die der
Ticket-Text nennt (`REGISTER_PATH` in `tests/contracts/test_identity_provider_verification.py`);
der Vertrag ist seit dem Ticket-Schnitt gewachsen. Der Nachweis gilt entsprechend für die acht.

## Die Durchgänge

### 1. `Location`-Header der 201 entfernt

Bruch: die Zeile `response.headers["Location"] = _SELF_URL` in
`src/api/identity/register_user_router.py` gelöscht.

Reaktion — `test_registration_fulfils_the_identity_contract` schlägt fehl, beide 201-Interaktionen
(„Registrierung mit freier E-Mail", „Registrierung mit einer Versatz-Zone"):

```
1.1) includes header 'Location' with value '"/api/v1/identity/me"'
       Expected header 'Location' to have value '"/api/v1/identity/me"' but was ''
```

### 2. `tokenType` von `"Bearer"` auf `"bearer"`

Bruch: der Literal-Typ in `src/api/identity/register_user_response.py` und der Wert im Router
kleingeschrieben.

Reaktion — dasselbe Testfall, wieder beide 201-Interaktionen, diesmal am Body:

```
has a matching body (FAILED)
  $.data.session.tokenType -> Expected 'bearer' (String) to be equal to 'Bearer' (String)
```

Die Groß-/Kleinschreibung eines einzigen Buchstabens genügt. `tokenType` ist matcherlos und damit
wörtlich bindend — genau wie der Ticket-Text es behauptet hatte.

### 3. Statuscode der Validierungsfehler von 422 auf 400

Bruch: `status.HTTP_422_UNPROCESSABLE_CONTENT` → `status.HTTP_400_BAD_REQUEST` im
`ValidationFailed`-Zweig des Routers.

Reaktion — **vier** Interaktionen fallen gleichzeitig, jede doppelt (Statuszeile und
`problem+json`-Körper, der den Status noch einmal trägt):

```
1.1) has a matching body
       $.status -> Expected 400 (Integer) to be equal to 422 (Integer)
1.2) has status code 422
       expected 422 but was 400
```

Betroffen: „Registrierung mit einem Passwort über der Obergrenze", „… auf Englisch gefragt",
„… mit ungültiger E-Mail, zu kurzem Passwort und zu kurzem Namen" und „… mit vergebener E-Mail und
zugleich ungültigen Feldern".

### 4. Gegenprobe: `meta.apiVersion` von `"1"` auf `"99"`

Bruch: `API_VERSION` in `src/middleware/response_envelope.py`.

Reaktion: **keine.** `2 passed`. Das ist kein Mangel, sondern der dokumentierte Vertragsstand —
`meta.*` ist typgeprüft, nicht wertgeprüft. Es ist aber der Punkt, an dem „Pact ist grün" nicht
mit „die Antwort ist richtig" verwechselt werden darf: eine falsche API-Version käme hier
ungebremst durch. Wer sie festnageln will, braucht einen eigenen Test — der Vertrag leistet es nicht.

### 5. Gegenprobe zur Gegenprobe: `Cache-Control: no-store` auf `no-cache`

Reaktion: rot, beide 201-Interaktionen:

```
Expected header 'Cache-Control' to have value 'no-store' but was 'no-cache'
```

Der Header ist also tatsächlich wertgebunden — Durchgang 4 ist keine generelle Blindheit des
Verifiers, sondern trifft genau die typgeprüften Felder.

## Fazit

**Abgesichert** ist alles, was der Vertrag matcherlos schreibt, und zwar zeichengenau: jeder
Statuscode, der `Location`-Header, `Cache-Control: no-store`, `tokenType: "Bearer"`, die
`data`/`meta`-Struktur der 2xx und das nackte `problem+json` der 4xx. Ein einzelnes falsches
Zeichen an diesen Stellen macht den Lauf rot. Die Verifikation ist damit ein echtes Netz und
keine Zeremonie.

**Nicht abgesichert** ist alles Typgeprüfte: Token- und Zeitwerte, `X-Request-Id`, sämtliche
`meta.*`-Werte sowie `title`, `detail`, `instance` und die Texte in `errors`. Dort prüft der
Verifier die Form, nicht den Inhalt. Und weil Pact Bodies als Teilmenge liest, fallen zusätzliche
Felder überhaupt nicht auf.

Daraus folgt für die künftigen Endpunkte: der Vertrag ersetzt keine Unit-Tests für die
*Bedeutung* der Werte. Er bindet die Grenze, nicht die Semantik dahinter. Wo ein Wert fachlich
stimmen muss, aber im Pact nur typgeprüft ist — Ablaufzeiten, `apiVersion`, die persistierte
Gültigkeit eines Refresh-Tokens —, gehört ein eigener Test dazu.

## Was das ausschließt

Es ersetzt nicht die Frage, ob der Vertrag selbst das Richtige verlangt — das bleibt
[`2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md`](2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md).
Und es begründet keine Mutationstest-Pflicht im CI: das Experiment war einmalig und von Hand;
seine Aussage steht in dieser Datei, nicht in einem Werkzeug.
