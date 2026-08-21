# Verträge (Pacts)

Hier liegen die Pact-Dateien, je Bounded Context ein Unterordner. Der Dateiname nennt beide Seiten:
`<consumer>-<provider>.json`.

Die Pacts des Frontends sind die **Vorgabe** der HTTP-Grenze dieses Backends, nicht deren Abbild —
siehe
[`docs/decisions/2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md`](../../docs/decisions/2026-08-21-1330-pacts-sind-die-vorgabe-der-http-grenze.md).
Sie kommen **von Hand** hierher: kein Pact Broker, kein Submodul, kein Zugriff auf das
Frontend-Repo. Das „go" je Vertrag gibt der Stakeholder, der die Datei auch ablegt.

Daneben stehen Pacts, deren Konsument dieses Repo selbst ist (`fit-back-…`). Sie sind keine
Vorgabe von außen, sondern belegen die Mechanik der Verifikation; wer sie ändert, ändert einen
Nachweis und keinen Vertrag.

Zu **jeder** Datei gehört eine Herkunftsnotiz in der `README.md` ihres Context-Ordners: woher sie
stammt, aus welchem Stand, und wann das „go" kam.

Verifiziert werden sie über `tests/contracts/` und damit über `./make.ps1 test` bzw. `ci`.
