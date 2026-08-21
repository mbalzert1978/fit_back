# Identity — Herkunft des Vertrags

## `nutritrack-app-nutritrack-identity.json`

| | |
|---|---|
| Consumer | `nutritrack-app` (Frontend) |
| Provider | `nutritrack-identity` |
| Pact-Spezifikation | V3 (erzeugt mit `pact-js` 17.1.2) |
| „go" des Stakeholders | 2026-08-21 |
| Abgelegt mit | `3ec8a8f` — *feat(contracts): Identity-Pact des Frontends ablegen* |
| Quell-Commit im Frontend | nicht mitgeliefert; die Datei kam von Hand, ohne Broker |

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
