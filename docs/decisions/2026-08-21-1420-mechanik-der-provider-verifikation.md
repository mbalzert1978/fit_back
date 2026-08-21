# Die Mechanik der Provider-Verifikation

**Entschieden am 2026-08-21, 14:20.** Umsetzung von
[#94](https://github.com/mbalzert1978/fit_back/issues/94). Baut auf
[`2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md`](./2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md)
auf: **dass** die Verträge die Vorgabe sind, steht dort; hier steht nur, **wie** sie geprüft werden.

## Was entschieden wurde

**Die Verifikation ist ein gewöhnlicher pytest-Test** unter `tests/contracts/`, kein eigenes
Gate. `./make.ps1 ci` ruft `test`, und `test` ruft `pytest` — damit hängt ein gebrochener Vertrag
automatisch im CI-Lauf, ohne dass irgendwo ein zweiter Einstiegspunkt gepflegt werden müsste.

**`pact-python` ≥ 3.4.0**, festgeschrieben statt `latest`. Verifiziert Pact-Spec V3 und passt
damit zu den Vertragsdateien des Frontends.

**Die Provider-States laufen in-process.** `Verifier.state_handler()` nimmt seit v3 ein Dict
`{state-name: handler}` entgegen und baut den HTTP-Wrapper selbst. Es kommt damit **keine
Test-Route nach `src/api/`** — kein Code am Rand, den es außerhalb der Verifikation nicht geben
dürfte.

**Die Mechanik liegt hinter einem Builder**, `tests/contracts/provider_verification.py`. Ein Test
sagt nur noch, was verifiziert wird:

```python
await (
    ProviderVerifikation.fuer("nutritrack-identity")
    .mit_vertrag(PACT_DATEI)
    .nur_interaktionen(NUR_REGISTRIERUNG)
    .mit_state(KEIN_KONTO, setup=konto.entfernen, teardown=konto.entfernen)
    .mit_state(KONTO_EXISTIERT, setup=konto.anlegen, teardown=konto.entfernen)
    .verifiziere(app)
)
```

Der Grund ist nicht Ästhetik: die Mechanik ist für alle sechs Verträge dieselbe, und ohne den
Builder stünde sie beim siebten Mal in sechs Kopien da. Der erste Anlauf hatte sie im Testmodul,
und das Ergebnis war unlesbar.

**Der Ausschluss ungebauter Endpunkte ist ein Regex auf die Beschreibung**
(`nur_interaktionen(r"^Registrierung ")`), nicht ein Umschreiben der Vertragsdatei. Der Vertrag
bleibt damit exakt so liegen, wie der Stakeholder ihn abgelegt hat, und das Aufmachen für
`login`/`refresh`/`logout`/`me` ist später eine Änderung an genau einer Zeile.

Weil der Ausdruck an fremdem Text hängt — die Beschreibungen schreibt der Consumer —, prüft ein
eigener Test, dass er genau die Interaktionen auf `/api/v1/identity/register` trifft und keine
andere. Ohne ihn könnte eine Umformulierung im Frontend den Filter ins Leere greifen lassen: der
Lauf wäre grün, weil er nichts mehr verifiziert. `set_error_on_empty_pact(enabled=True)` fängt den
Totalausfall zusätzlich ab.

**Setup und Teardown sind getrennt, und der Teardown räumt wirklich auf.** Vier der fünf
Interaktionen tragen denselben State, und eine davon legt das Konto tatsächlich an; bliebe es
stehen, bekäme die nächste 409 statt 201. Ein zweiter Test löst genau das aus, statt es zu
behaupten.

**Die State-Handler seeden direkt gegen `identity.users`**, über die vorhandene
`postgres_engine`-Fixture — nicht über den Endpunkt, den die Verifikation gerade prüft. Ein State,
der sich auf sein eigenes Prüfobjekt stützt, belegt nichts.

## Ein Fallstrick, der Zeit gekostet hat

Pact ruft die State-Handler aus dem Thread seines eigenen kleinen HTTP-Servers heraus auf. Die
Engine des Tests gehört aber dessen Event-Loop; von einem fremden Thread aus benutzt, fällt asyncpg
um. Die Lösung steht als `Schleifenbruecke` im Builder: `verify()` läuft seinerseits in einem
Thread (`asyncio.to_thread`), womit die Loop des Tests frei ist, und die Handler reichen ihre Arbeit
über `run_coroutine_threadsafe` dorthin zurück.

Zweiter Fallstrick derselben Bauart: `while not server.started` hängt für immer, wenn die App beim
Start abbricht — etwa weil die DB-Umgebungsvariablen fehlen. Die Schleife wartet deshalb auch auf
`thread.is_alive()` und wirft, statt zu hängen.

## Der Zustand am Ende dieses Tickets

**Der Lauf ist rot, und das ist das Fertig-Kriterium.** Die Ausgabe benennt die fünf
Register-Interaktionen als das, was noch nicht erfüllt ist — abweichende `type`-URIs, 400 statt
422, fehlende `data`/`meta`-Hüllen, fehlende `Location`- und `X-Request-Id`-Header. Kein
Aufsetzfehler; grün wird der Lauf mit dem Ticket, das `POST /api/v1/identity/register` an den
Vertrag heranbaut.

## Was dadurch ersetzt wird

Der Mechanismus aus `docs/milestones/02-test-pyramide.md`, „Form B" — handgeschriebene
Beispiel-Payloads unter `contexts/<producer>/contracts/events/<event>/examples/*.json` samt
Roundtrip-Test — ist zurückgenommen. Pact tritt **nicht** an seine Stelle: dessen Umfang ist die
HTTP-Grenze, und Context-zu-Context-Ereignisse laufen heute in einem Prozess. Für Integration
Events aus der Outbox ist damit keine Form entschieden; die Test-Pyramide führt sie jetzt als
offenen Punkt „Form C". Der Verweis auf dieses Ticket in `.rules/python/python-feature-slices.md`
ist weg, `specs/contracts/` bleibt für „Form A" reserviert (Contract-Tests gegen ein
aufrufer-eigenes Port-`Protocol`).

## Was ausdrücklich nicht entschieden wurde

- **Ein Pact Broker.** Vertagt, nicht verworfen — interessant, sobald `can-i-deploy` oder
  Pending-/WIP-Pacts gebraucht werden. Beides setzt ein Deployment voraus, das es nicht gibt.
- **Die Erfüllung des Vertrags.** Inhalt des Register-Tickets.
- **Die fünf übrigen Verträge** (catalog, diary, goals, recipes, health). Sie entstehen mit ihren
  Contexts; der Builder trägt sie ohne Änderung.
