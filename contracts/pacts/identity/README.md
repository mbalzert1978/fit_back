# Identity — Herkunft der Pacts

## `nutritrack-app-nutritrack-identity.json`

| | |
|---|---|
| Consumer | `nutritrack-app` (Frontend) |
| Provider | `nutritrack-identity` |
| Pact-Spezifikation | V3 (erzeugt mit `pact-js` 17.1.2) |
| „go" des Stakeholders | 2026-08-21 |
| Abgelegt mit | `3ec8a8f` — *feat(contracts): Identity-Pact des Frontends ablegen* |
| Quell-Commit im Frontend | **entfällt bewusst** — siehe unten |

**Zum entfallenden Quell-Commit.** Die Zeile ist keine offene Aufgabe. Der Pact wurde von Hand
übergeben, ohne Broker und ohne Zugriff auf das Frontend-Repository — beides ist so entschieden
([`docs/decisions/2026-08-21-1420-mechanik-der-provider-verifikation.md`](../../../docs/decisions/2026-08-21-1420-mechanik-der-provider-verifikation.md),
„Ein Pact Broker" unter *Was ausdrücklich nicht entschieden wurde*). Damit gibt es keinen
Commit-Zeiger, den dieses Repo aufschreiben könnte, und keinen, den jemand später nachtragen
kann. Was die Herkunft trägt, sind die beiden Zeilen darüber: das „go" des Stakeholders vom
2026-08-21 und der Commit, mit dem die Datei hier landete. Erst wenn ein Broker dazukommt, gibt
es überhaupt eine Quelle, auf die zu verweisen wäre; bis dahin ist die Zeile beantwortet, nicht
leer.

Elf Interaktionen. Verifiziert werden davon zurzeit nur die fünf für
`POST /api/v1/identity/register` (201 ×2, 422 ×2, 409); `login`, `refresh`, `logout` und `me` sind
noch nicht gebaut und bleiben über den Filter in
[`tests/contracts/test_identity_provider_verification.py`](../../../tests/contracts/test_identity_provider_verification.py)
draußen, bis ihr jeweiliges Ticket kommt.

**Befund für die Consumer-Seite:** die Provider-States backen ihre Daten in den Namen
(`"Nutzer a@b.de existiert mit Passwort geheim123"`), statt sie als V3-`parameters` zu führen. Das
erzwingt einen Handler je Datensatz statt einen je Zustandsart — für die zwei Register-States
folgenlos, über alle Verträge hinweg der Unterschied zwischen einer Handvoll Handlern und dreißig.
Ändern kann das nur der Consumer.

## `fit-back-mechanik-nutritrack-identity.json`

| | |
|---|---|
| Consumer | `fit-back-mechanik` — **dieses Repo**, kein Stakeholder |
| Provider | `nutritrack-identity` |
| Pact-Spezifikation | V3, von Hand geschrieben |
| Angelegt mit | [#94](https://github.com/mbalzert1978/fit_back/issues/94) |

**Keine Vorgabe, sondern ein Nachweis.** Zwei Interaktionen auf
`POST /api/v1/identity/register`, die sich einen Provider-State teilen und beide 409 erwarten — eine
Form, die die App heute schon erfüllt. Räumt der Teardown des States nicht auf, läuft das zweite
Setup in den `uq_users_email` und der Lauf wird rot; genau das belegt er. Er läuft deshalb **grün**,
während der Vertrag des Frontends noch rot ist, und ist der einzige Weg, die Mechanik zu prüfen,
solange sie nichts Erfülltes zu prüfen hat.

Wer ihn ändert, ändert einen Nachweis. Sein Wert hängt daran, dass der geteilte State das Konto
wirklich **anlegt** — bei einem aufräumenden State wäre er wertlos, siehe
[`docs/decisions/2026-08-21-1420-mechanik-der-provider-verifikation.md`](../../../docs/decisions/2026-08-21-1420-mechanik-der-provider-verifikation.md).
