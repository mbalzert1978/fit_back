# M7 — HealthSync

**Bezug BACKEND.md:** Abschnitt 6, Abschnitt 8.7.
**Voraussetzung:** M1 (Nutzeridentität), M4 (liefert den `activities`-Block der Tagesansicht nach).

## Ziel

Entgegennahme von Aktivitätsdaten vom Gerät (Apple Health/Health Connect), Bereitstellung für die
Tagesansicht. Das Backend spricht nicht selbst mit HealthKit.

## Scope

Aggregates: `DailyActivity` (Upsert je `ExternalId`), `HealthConsent`.

API: `PUT/GET /api/v1/health/activity/{date}`, `GET/PATCH /api/v1/health/consent`,
`GET /api/v1/health/nutrition-export/{date}`.

## Nachzügler: Diary-`activities`-Block

M4 liefert bereits das (leere) `activities`-Feld in der Tagesansicht. Dieses Ticket schließt die
Lücke: `Diary.GetDay` liest `DailyActivity` für Tag+Nutzer und befüllt das Feld — ein kleiner,
eigenständiger Integrations-Slice zwischen den beiden Contexts (Application-Service-Aufruf, kein
Tabellenzugriff über Context-Grenzen hinweg, siehe Abschnitt 0.5/Abschnitt 0-Cross-Cutting-Regel).

## Tests (Abschnitt 9)

- Domain-Unit-Test: Upsert per `ExternalId` erzeugt keine Dubletten bei wiederholtem Hochladen.
- Value-Object-Tests (`ActivityName`, `ActivityDetail`, `Energy`).
- Tagged-Union-Serialisierungstest (`Connection`: `NotConnected`/`Connected`).
- Integrationstest: `Diary.GetDay` mit vorhandener `DailyActivity` befüllt `activities` korrekt;
  ohne Verbindung bleibt es leer.
- Integrationstests je Endpunkt, `curl`-Beispiele.
