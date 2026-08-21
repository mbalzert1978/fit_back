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
    ProviderVerifikation.fuer("nutritrack-identity", identity_pact)
    .nur_pfade(REGISTER_PFAD)
    .mit_state(KEIN_KONTO, setup=konto.entfernen, teardown=konto.entfernen)
    .mit_state(KONTO_EXISTIERT, setup=konto.anlegen, teardown=konto.entfernen)
    .verifiziere(app, pact_ablage)
)
```

Der Grund ist nicht Ästhetik: die Mechanik ist für alle sechs Verträge dieselbe, und ohne den
Builder stünde sie beim siebten Mal in sechs Kopien da. Der erste Anlauf hatte sie im Testmodul,
und das Ergebnis war unlesbar.

**Der Ausschluss ungebauter Endpunkte läuft über den Pfad** (`nur_pfade("/api/v1/identity/register")`),
nicht über ein Umschreiben der Pact-Datei. Sie bleibt exakt so liegen, wie der Stakeholder sie
abgelegt hat, und das Aufmachen für `login`/`refresh`/`logout`/`me` kostet eine Zeile plus die
States, die die neuen Interaktionen tragen.

Pact selbst filtert nur über die **Beschreibung**. Statt daraus ein Muster zu bauen, spielt der
Builder einen **reduzierten Pact** ab: eine Kopie im Temp-Ordner, die nur die gewählten
Interaktionen trägt. Damit gibt es keinen Regex mehr, der danebengreifen könnte, und die Datei des
Stakeholders bleibt unberührt.

Die Form eines Pacts wird an genau einer Stelle gedeutet (`Pact.von`). `Interaktion` trägt
`beschreibung`, `pfad` und die rohe Nutzlast und entscheidet über `zeigt_auf(pfade)` selbst, ob sie
dazugehört; `Pact.nur_auf(pfade)` gibt den reduzierten Pact zurück. `Any` kommt in keiner Signatur
und keinem Feld vor — was aus JSON kommt, ist `object` und wird über `_als(wert, art, wo)` geprüft,
das im Fehlerfall den Feldnamen nennt.

**Das Dateisystem berührt nur die `conftest.py`.** Sie ist die einzige Stelle unter
`tests/contracts/`, die `json` importiert und eine Datei öffnet: die Fixtures `identity_pact` und
`mechanik_pact` reichen fertige `Pact`-Objekte herein, `pact_ablage` reicht die Funktion, die den
reduzierten Pact nach `tmp_path` schreibt (pytest räumt ihn selbst weg — kein `tempfile` mehr im
Baukasten). Weder ein Testmodul noch der Baukasten weiß damit, wo die Pacts liegen oder dass es
Dateien sind; austauschbar ist beides über eine Fixture statt über einen Patch.

`pfad` ist ein `PurePosixPath` — kein String, weil der Typ `/a//b` und `/a/b` gleich vergleicht;
kein `Path`, damit unter Windows keine Backslash-Semantik hereinrutscht; und kein URL-Typ, weil im
Pact ein Pfad steht und sonst nichts. Schema, Host und Query blieben leer und würfen die Frage auf,
gegen welchen Host verglichen wird.

Zwei Zwischenschritte hatten es anders versucht. Der erste pflegte ein Muster (`^Registrierung `)
von Hand und stellte die Zahl der Treffer als `erwartet=5` daneben. Das war schwächer, als es aussah: benennt der Consumer eine
`login`-Interaktion in „Registrierung …" um und eine `register`-Interaktion weg, sind es weiterhin
fünf — und ein ungebauter Endpunkt liefe mit. Die Zahl prüfte ein Symptom, der Pfad prüft die
Sache. Findet ein Pfad keine Interaktion, bricht der Aufbau ab;
`set_error_on_empty_pact(enabled=True)` fängt den Totalausfall zusätzlich.

**Setup und Teardown sind getrennt, und der Teardown räumt wirklich auf.** Vier der fünf
Register-Interaktionen tragen denselben State `Keine Registrierung mit a@b.de vorhanden`. **Zwei
davon erwarten 201 und legen `a@b.de` dabei selbst an — über den Endpunkt, nicht über den
State-Handler.** Der Handler dieses States legt nichts an; er stellt eine *Abwesenheit* her und
räumt in beiden Hälften ab. Bliebe das Konto der ersten 201 stehen, bekäme die zweite 409 statt
201. Die fünfte Interaktion trägt `Nutzer a@b.de existiert mit Passwort geheim123`, erwartet 409,
und erst dort legt der Setup-Handler das Konto an, während der Teardown es wieder entfernt.

Daran hängt die Trennung: die beiden Hälften tun je nach State verschiedene Arbeit —
`entfernen`/`entfernen` beim einen, `anlegen`/`entfernen` beim anderen. Ein einziger Handler je
State könnte das nicht ausdrücken, und ein aufräumender Teardown ist auch dort nötig, wo der
Zustand über den geprüften Endpunkt entstanden ist statt über den Handler.

Belegt wird das über einen **zweiten, grünen Verifikationslauf** gegen einen kleinen Pact, dessen
Konsument dieses Repo selbst ist
(`contracts/pacts/identity/fit-back-mechanik-nutritrack-identity.json`): zwei Interaktionen, die
sich den *anlegenden* State teilen, beide 409 erwartend — eine Form, die die App heute schon
erfüllt. Räumt der Teardown nicht, läuft das zweite Setup in den `uq_users_email` und der Lauf wird
rot. Nachgeprüft mit ausgehebeltem Teardown: er wird es.

Der Umweg über einen eigenen Pact ist der Punkt. Der Lauf gegen den echten Vertrag ist rot und kann
deshalb **nichts** belegen; ein Nachweis, der die Handler von Hand aufruft, prüft die Mechanik am
Prüfobjekt vorbei. Der Mechanik-Pact prüft denselben Weg mit derselben Verdrahtung, nur grün — und
liest sich im Testmodul genau wie der echte Lauf.

Der State ist mit Absicht der anlegende: bei `Keine Registrierung mit a@b.de vorhanden` räumt schon
das Setup auf, dort wäre der Teardown folgenlos und der Nachweis wertlos. Ein erster Anlauf hatte
genau diesen Fehler und fiel bei der Gegenprobe auf.

**Die State-Handler seeden direkt gegen `identity.users`**, über die vorhandene
`postgres_engine`-Fixture — nicht über den Endpunkt, den die Verifikation gerade prüft. Ein State,
der sich auf sein eigenes Prüfobjekt stützt, belegt nichts.

## Ein Fallstrick, der Zeit gekostet hat

Pact ruft die State-Handler aus dem Thread seines eigenen kleinen HTTP-Servers heraus auf. Die
Engine des Tests gehört aber dessen Event-Loop; von einem fremden Thread aus benutzt, fällt asyncpg
um. Die Lösung steht als `_handler_auf(...)` im Builder: `verify()` läuft seinerseits in einem
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

Damit das nicht bloß behauptet ist, hier der Beleg — Ausgabe von `./make.ps1 test`, gekürzt auf
das, was das Kriterium trägt; Laufzeiten, Pfade und Wiederholungen sind heraus, der Rest steht
wörtlich. Nur die **Reihenfolge** ist hier alphabetisch geordnet statt abgeschrieben: Pact gibt
Header und Body-Abweichungen je Lauf in wechselnder Folge aus — zwei Läufe desselben Standes
unterscheiden sich darin, sonst in nichts. Eine feste Ordnung macht den Auszug vergleichbar:

```text
Verifying a pact between nutritrack-app and nutritrack-identity

  Registrierung mit einer Versatz-Zone
     Given Keine Registrierung mit a@b.de vorhanden
    returns a response which
      has status code 201 (FAILED)
      includes headers
        "Cache-Control" with value "no-store" (FAILED)
        "Content-Type" with value "application/json" (FAILED)
        "Location" with value "/api/v1/identity/me" (FAILED)
        "X-Request-Id" with value "01JQ8Z3K7V9XW2P4M6N8R0T5YB" (FAILED)
      has a matching body (FAILED)

  Registrierung mit freier E-Mail
     Given Keine Registrierung mit a@b.de vorhanden
    returns a response which
      has status code 201 (OK)
      includes headers
        ... (drei der vier Header weichen ab, gekürzt)
      has a matching body (FAILED)

  Registrierung mit ungültigen Angaben, auf Englisch gefragt
     Given Keine Registrierung mit a@b.de vorhanden
    returns a response which
      has status code 422 (FAILED)
      ...
      has a matching body (FAILED)

  Registrierung mit ungültiger E-Mail, zu kurzem Passwort und zu kurzem Namen
     Given Keine Registrierung mit a@b.de vorhanden
    returns a response which
      has status code 422 (FAILED)
      ...
      has a matching body (FAILED)

  Registrierung mit vergebener E-Mail
     Given Nutzer a@b.de existiert mit Passwort geheim123
    returns a response which
      has status code 409 (OK)
      ...
      has a matching body (FAILED)

Failures:

1) ... Registrierung mit einer Versatz-Zone
    1.1) has a matching body
           $ -> Actual map is missing the following keys: data, meta
    1.2) has status code 201
           expected 201 but was 400
2) ... Registrierung mit freier E-Mail
    2.1) has a matching body
           $ -> Actual map is missing the following keys: data, meta
3) ... Registrierung mit ungültigen Angaben, auf Englisch gefragt
    3.1) has a matching body
           $.status -> Expected 400 (Integer) to be equal to 422 (Integer)
           $.type -> Expected 'https://api.example/errors/validation-failed' (String) to be equal
                     to 'tag:nutritrack.app,2026:problems/validation-failed' (String)
4) ... Registrierung mit ungültiger E-Mail, zu kurzem Passwort und zu kurzem Namen
    4.1) has a matching body
           $.errors -> Actual map is missing the following keys: displayName
5) ... Registrierung mit vergebener E-Mail
    5.1) has a matching body
           $.type -> Expected 'https://api.example/errors/email-already-registered' (String) to be
                     equal to 'tag:nutritrack.app,2026:problems/email-already-registered' (String)

There were 5 pact failures

FAILED tests/contracts/test_identity_provider_verification.py::test_die_registrierung_erfuellt_den_identity_vertrag
1 failed, 282 passed
```

Abzulesen ist daran genau das Kriterium: **fünf** Register-Interaktionen, jede unter ihrem
`Given …` — die State-Handler sind also gelaufen, sonst gäbe es die Zeile nicht —, und jede
scheitert an einer Zusicherung des Vertrags (Status, Header, Body), nicht am Aufbau des Laufs.
Ein Aufsetzfehler sähe anders aus: er bräche vor der ersten Interaktion ab, und keine der fünf
stünde da. Die übrigen 282 Tests bleiben grün, der Mechanik-Lauf darunter.

## Was dadurch ersetzt wird

Der Mechanismus aus `docs/milestones/02-test-pyramide.md`, „Form B" — handgeschriebene
Beispiel-Payloads unter `contexts/<producer>/contracts/events/<event>/examples/*.json` samt
Roundtrip-Test — ist zurückgenommen. Pact tritt **nicht** an seine Stelle: dessen Umfang ist die
HTTP-Grenze, und Context-zu-Context-Ereignisse laufen heute in einem Prozess. Für Integration
Events aus der Outbox ist damit keine Form entschieden; die Test-Pyramide führt sie jetzt als
offenen Punkt „Form C". Der Verweis auf dieses Ticket in `.rules/python/python-feature-slices.md`
ist weg, `specs/contracts/` bleibt für „Form A" reserviert (Contract-Tests gegen ein
aufrufer-eigenes Port-`Protocol`).

## Was der Review noch geradegerückt hat

- **Der Seed lief in Millisekunden.** `registered_at` führt in diesem Repo Unix-**Sekunden**
  (`2026-08-06-1340-unix-epoch-statt-datetime.md`); der erste Wurf schrieb `1_700_000_000_000` und
  damit das Jahr 55840. Heute folgenlos — keine der fünf Interaktionen liest den Wert —, aber falsch.
- **`Testkonto.anlegen()` räumte vorher selbst auf.** Damit war der Teardown-Nachweis nicht tragend:
  man hätte den Teardown streichen können und der Test wäre grün geblieben. `anlegen()` läuft jetzt
  ungeschützt in den `uq_users_email` — genau das ist der Fall, den der Nachweis auslösen soll.
- **Der Nachweis ging an der echten Verdrahtung vorbei.** Er fährt jetzt über den echten `Zustand`,
  und ein zweiter, winziger Test deckt die Zuordnung `setup`/`teardown` ab, mit der Pact ruft.
- **„Vertrag" war schon vergeben.** `CONTEXT.md` führt den Begriff für das veröffentlichte Vokabular
  eines Context. Der Pact ist ein anderes Ding und heißt jetzt im Glossar wie im Code **Pact**.

## Komposition, nicht Vererbung

Der Builder ist für alle sechs Verträge gedacht. Die naheliegende Frage war, ob die Wiederverwendung
nicht als abstrakte Test-Basisklasse gehört, von der jeder Context erbt. **Nein**, und das Kriterium
ist:

Eine geerbte Test-Basis ist richtig, wenn **N Implementierungen dieselbe Suite erfüllen** müssen —
eine Suite, mehrere Prüflinge (der Fall, den `02-test-pyramide.md` unter „Form A" beschreibt: eine
Contract-Suite gegen ein Port-`Protocol`, ausgeführt gegen jeden Adapter).

Hier ist es umgekehrt: sechs Contexts, sechs verschiedene Pacts, verschiedene Endpunkte,
verschiedene States. Es gibt **keine gemeinsame Zusicherung** zu erben. Geteilt ist allein die
Maschinerie — App hochfahren, States verdrahten, Pact abspielen —, und dafür ist Komposition der
Weg. Eine Basisklasse zwänge jedes Testmodul in eine Unterklasse, mit Hooks und fremdem
Lebenszyklus, für null geteiltes Verhalten.

Kippen würde das, sobald *jeder* Context-Lauf zusätzlich etwas belegen muss — etwa
State-Unabhängigkeit. Dann gäbe es genau einen geerbten Test und die Basisklasse wäre richtig.
Heute existiert nur Identity; das jetzt zu bauen wäre Vorrat auf Verdacht.

## Was ausdrücklich nicht entschieden wurde

- **Ein Pact Broker.** Vertagt, nicht verworfen — interessant, sobald `can-i-deploy` oder
  Pending-/WIP-Pacts gebraucht werden. Beides setzt ein Deployment voraus, das es nicht gibt.
- **Die Erfüllung des Vertrags.** Inhalt des Register-Tickets.
- **Die fünf übrigen Verträge** (catalog, diary, goals, recipes, health). Sie entstehen mit ihren
  Contexts; der Builder trägt sie ohne Änderung.
