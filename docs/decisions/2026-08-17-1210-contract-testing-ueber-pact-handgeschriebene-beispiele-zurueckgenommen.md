# Contract-Testing läuft über Pact — die handgeschriebenen Beispiel-Payloads sind zurückgenommen

**Anlass:** Review zu [PR #91](https://github.com/mbalzert1978/fit_back/pull/91) (Ticket
[#51](https://github.com/mbalzert1978/fit_back/issues/51), Stufe 4).

## Was entschieden wurde

**Contract-Testing läuft in diesem Repo über [Pact](https://github.com/pact-foundation/pact-python),
consumer-driven, vom Frontend nach unten.** Vorgabe des Stakeholders im Review.

Die in PR #91 gebauten Artefakte des selbstgebauten Verfahrens sind damit der falsche Mechanismus
und wurden aus dem PR **wieder entfernt**:

- `src/contexts/identity/contracts/events/user_registered/examples/v1-vollstaendig.json`
- `src/contexts/identity/contracts/events/user_registered/README.md`
- `src/contexts/identity/specs/contracts/test_user_registered_contract.py` (+ `__init__.py`)
- die Docstring-Absätze in `contracts/user_registered.py` und `domain/events.py`, die den
  Beispielordner zum **verbindlichen** Vertrag erklärten

**Nicht** zurückgenommen wurde die Nutzlast selbst: `UserRegistered` trägt weiter die fünf Felder
`userId`, `email`, `locale`, `timeZoneId`, `registeredAt`. Welche Felder ein Ereignis trägt,
entscheidet der Bedarf der Konsumenten, nicht das Prüfverfahren — der Einwand richtete sich gegen
den Mechanismus, nicht gegen den Feldbestand.

Die offenen Grundsatzfragen (wer ist Consumer bei Context-zu-Context-Ereignissen, wo steht der
Broker, wie hängt es in der CI, was gilt in der Zwischenzeit, wo lebt die Versionierung) sind als
Ticket [#94](https://github.com/mbalzert1978/fit_back/issues/94) angelegt und werden **nicht** in
#91 beantwortet.

## Warum nicht sofort umgebaut

**Pact existiert im Repo heute nirgends** — keine Abhängigkeit in `pyproject.toml`, kein Code, kein
Broker. Es gibt also nichts, wogegen der Slice sofort umgebaut werden könnte. Ein Geräst „auf
Vorrat" wäre eine Vorwegnahme der Entscheidung, die #94 erst treffen soll.

Der Preis der Rücknahme ist benannt: die Feldmenge des veröffentlichten Ereignisses ist bis #94
**nur** durch die Slice-Specs gedeckt, nicht durch einen Vertrag. Das ist ein bewusst
hingenommener, dokumentierter Zwischenzustand — kein Versehen.

## Was das für Ticket #51 bedeutet

Das Fertig-Kriterium „Contract-Test (Form B)" aus Stufe 2 von #51 ist **überholt**. Es verlangte
wörtlich kanonische Beispiel-Payloads als `.json`-Dateien plus einen Roundtrip-Test — also genau den
Mechanismus, der jetzt fällt. #51 gilt mit dem Merge von #91 als erfüllt, **ohne** diesen Punkt; er
wandert nach #94.

Ebenfalls überholt und in #94 nachzuziehen: `docs/milestones/02-test-pyramide.md` beschreibt „Form
B" als Beispiel-Payloads unter `contexts/<producer>/contracts/events/<event>/examples/*.json`. Diese
Datei wurde hier **nicht** angefasst — sie umzuschreiben hieße, die Antwort zu erfinden, die #94
erst gibt.

## Greptile-Befund `user_id` → `userId`: heute gegenstandslos, mit Beleg

Greptile hat (P2) angemerkt, dass die Nutzlast unter **unverändertem** `EVENT_TYPE = "UserRegistered"`
umbenannt und erweitert wurde:

```
vorher:  {"user_id": …, "locale": …}
nachher: {"userId": …, "email": …, "locale": …, "timeZoneId": …, "registeredAt": …}
```

Der Befund ist **formal richtig** und trifft die eigene Zusage des Docstrings („Umbenennen oder
Entfernen ist ein Bruch und braucht ein eigenes Ticket, das die Konsumenten mitzieht"). Er ist
heute dennoch **gegenstandslos**, und zwar nicht aus Bequemlichkeit, sondern messbar:

- **Es gibt keinen registrierten Konsumenten.** `EventRegistry.register(...)`
  (`shared_kernel/events.py:132`) hat im gesamten `src/` **keine** produktive Aufrufstelle — nur
  Erwähnungen in Docstrings. Goals (M2, #58) und Diary (M4, #66) sind ungebaut und blockiert.
- **Es gibt kein Deployment.** Der Stack läuft ausschließlich lokal über `docker-compose.yml`
  (postgres/minio/app); Postgres-Instanzen in Tests sind ephemere Testcontainer. Persistente
  Outbox-Zeilen im alten Format kann es außerhalb eines lokalen Dev-Volumes nicht geben, und dort
  löst `docker compose down -v` sie auf.

Greptiles Prämisse lautet „if pre-merge outbox rows remain pending **when a consumer is
registered**". Beide Hälften sind heute nicht gegeben. Deshalb wird **keine** Wire-Level-Version
eingeführt: sie wäre Infrastruktur gegen ein Szenario, das nicht existieren kann, und würde
vermutlich am falschen Ort landen — wo Versionierung lebt, hängt an der Pact-Entscheidung.

**Ab dem ersten echten Konsumenten gilt das nicht mehr.** Der Befund ist deshalb nicht verworfen,
sondern nach #94 verschoben und dort als Acceptance-Kriterium geführt. Der `!`-Marker im PR-Titel
kündigt den Bruch an; er behandelt ihn nicht — das ist gewollt, solange es nichts zu behandeln gibt.

## Was dadurch ausgeschlossen wird

- Kein zweites, parallel gepflegtes Contract-Verfahren neben Pact. Der handgeschriebene
  Beispielordner kommt nicht zurück.
- Keine Wire-Level-Versionierung der Ereignis-Nutzlast, bevor #94 entschieden hat, wo sie hingehört.
- Kein Pact-Geräst ohne echten Vertrag: #94 verlangt ausdrücklich mindestens einen laufenden
  Vertrag, nicht ein Skelett.
