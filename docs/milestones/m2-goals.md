# M2 — Goals & Preferences

**Bezug BACKEND.md:** Abschnitt 5, Abschnitt 8.2.
**Voraussetzung:** M1 (konsumiert `UserRegistered`).

## Ziel

Tagesziel, Makroverteilung, Rundungs-/Brennwertregeln, Darstellungseinstellungen — inklusive des
Default-Zielprofils, das `Diary` (M4) für die Tagesansicht braucht.

## Scope

Aggregates: `NutritionGoal` (eins pro Nutzer), `AppPreferences` (eins pro Nutzer).

Use Cases: Default-Profil-Erzeugung als Event-Handler auf `UserRegistered` (aus M1), `GetGoals`,
`UpdateGoals` (Gramm⇄Prozent-Ableitung, Konsistenzregel Prozentsumme ≠ 100 als gültiger
Zwischenzustand), `GetPreferences`, `UpdatePreferences`.

API: `GET /api/v1/goals`, `PUT /api/v1/goals`, `GET /api/v1/preferences`,
`PATCH /api/v1/preferences`.

## Cross-Cutting-Check

- Rundung (Regel 2) wird hier **implementiert** (`RoundingDirection`-Union mit `Apply`-Verhalten je
  Fall) — jeder spätere Meilenstein, der aggregierte Tageswerte ausgibt (M4), konsumiert diese
  Implementierung, statt eigene Rundungslogik zu bauen.
- `EnergyFactors`-Union (Physiological/Declaration) wird hier implementiert; M4 und M6 nutzen sie
  nur, definieren sie nicht neu.

## Tests (Abschnitt 9)

- Domain-Unit-Tests: Gramm⇄Prozent-Ableitung, Konsistenzregel (Summe ≠ 100 ⇒ kein Fehler, nur kein
  Neu-Errechnen von `DailyKcal`).
- Rundungstabelle: `Up`/`Down` × `Physiological`/`Declaration`, Assertion „nie eine
  Nachkommastelle in einer berechneten Ausgabe".
- Value-Object-Tests (`DailyKcal`-Range, `Percentage`, `MacroDistribution`).
- Tagged-Union-Serialisierungstests (`EnergyFactors`, `RoundingDirection`, `Theme`, `Language`).
- Integrationstest: `UserRegistered` erzeugt tatsächlich ein Default-Zielprofil (End-to-End über
  M1 + M2).
