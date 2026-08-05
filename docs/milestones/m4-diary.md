# M4 — Diary: Slots, Tag, Einträge, Tagesaggregation

**Bezug BACKEND.md:** Abschnitt 3, Abschnitt 8.4.
**Voraussetzung:** M1 (Nutzeridentität, Standard-Slots auf `UserRegistered`), M2 (Ziel/Rundung für
`goal`-Block der Tagesansicht), M3 (`ProductId`/`NutrientsPer100`-Kopiersemantik beim Erfassen).

## Ziel

Mahlzeiten-Slots, Tageseinträge, Tagesaggregation, Planung künftiger Tage. Das zentrale
„schnelle Datenerfassung"-Erlebnis der App.

## Scope

Aggregates: `MealSlot`, `DiaryDay` (mit `DiaryEntry` als Child-Entity).

Use Cases: `GetDay`, `AddEntry`, `UpdateEntryAmount`, `MoveEntry`, `DeleteEntry`, `ListSlots`,
`CreateSlot`, `RenameSlot`, `ReorderSlots`, `DeleteSlot`, `GetRecent`.

Event-Handler auf `UserRegistered` (aus M1): drei Standard-Slots (Frühstück, Mittagessen,
Abendessen, in dieser Reihenfolge).

API: `GET /api/v1/diary/days/{date}`, `POST/PATCH/DELETE .../entries[/{id}][/slot]`,
`GET/POST/PATCH/PUT/DELETE /api/v1/diary/slots...`, `GET /api/v1/diary/recent`.

`activities`-Block der Tagesansicht (aus HealthSync) ist an dieser Stelle **immer leer** — der
Draft sagt „leer wenn nicht verbunden", HealthSync existiert als Context erst ab M7; das Feld
selbst gehört ins Response-Schema von M4, sein tatsächlicher Inhalt kommt aus M7 (siehe
`m7-healthsync.md`, Abschnitt „Nachzügler").

## Cross-Cutting-Check

- **Kopiersemantik** (Abschnitt 3, „Nährwerte werden kopiert, nicht referenziert") ist die
  zentrale Invariante dieses Meilensteins — expliziter Test: Produkt nach Erfassung ändern ⇒ alter
  Tagebucheintrag unverändert.
- **Zusammenfassen gleicher Einträge** (gleicher Slot, gleicher Tag, gleiche `SourceId`) ⇒ Gramm
  addieren statt neue Zeile, Antwort `200` statt `201`.
- Rundung (aus M2) wird hier auf `computed`/`totals`/`goal.effectiveKcal` angewendet;
  `nutrientsPer100` bleibt ungerundet.

## Nicht in Scope

- `EntrySource.FromRecipe` ist als Typ bereits Teil der Union (Abschnitt 0.11 — geschlossene
  Typhierarchie von Anfang an vollständig), aber ungenutzt, bis M6 den Recipes-Context liefert und
  `portions-to-diary` intern `AddEntry` mit diesem Fall aufruft.
- Der `activities`-Inhalt aus HealthSync (s. o.) — nur das leere Datenschema.

## Tests (Abschnitt 9)

- Domain-Unit-Tests je Invariante (`MealSlot` nicht löschbar mit Einträgen, `Position` lückenlos,
  Zukunft max. 14 Tage, Zusammenfassen-Regel, Verschieben mit Zusammenfassen).
- **Kopiersemantik-Test** (explizit in Abschnitt 9 gefordert): Produkt ändern ⇒ alter Eintrag
  unverändert.
- **Zusammenfassen-Test** (explizit gefordert): zweimal dasselbe Produkt in denselben Slot ⇒ ein
  Eintrag mit addierten Gramm.
- Value-Object-Tests (`Grams`, `PortionLabel`, `SlotName`, `SlotPosition`) + Architekturtest.
- Tagged-Union-Serialisierungstest (`EntrySource`).
- Idempotenz-Test für `POST .../entries`.
- Integrationstests je Endpunkt inkl. Fehlerfälle (`grams-out-of-range`, `meal-slot-not-found`,
  `source-not-found`, `date-too-far-in-future`, `slot-not-empty`), zusätzlich `curl`-Beispiele.
