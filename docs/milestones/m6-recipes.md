# M6 — Recipes

**Bezug BACKEND.md:** Abschnitt 4, Abschnitt 8.6.
**Voraussetzung:** M3 (Zutaten entstehen ausschließlich aus `Product`), M4 (`portions-to-diary`
ruft intern `Diary.AddEntry` mit `EntrySource.FromRecipe`).

## Ziel

Nutzereigene Rezepte aus mehreren Zutaten, Portionierung, Ableitung von `NutrientsPer100`.

## Scope

Aggregate: `Recipe` (mit `RecipeIngredient`-Entities).

Use Cases: `ListRecipes`, `GetRecipe`, `CreateRecipe`, `UpdateRecipe`, `DeleteRecipe`,
`AddIngredient`, `UpdateIngredientGrams`, `RemoveIngredient`, `PortionsToDiary`.

API: `GET/POST /api/v1/recipes`, `GET/PUT/DELETE /api/v1/recipes/{id}`,
`POST /api/v1/recipes/{id}/portions-to-diary`.

## Cross-Cutting-Check

- Normalisierung auf `NutrientsPer100` beim Speichern (Abschnitt 4) — dieselbe
  `NutrientsPer100`-Invariantenprüfung wie in M3 wiederverwendet, nicht neu implementiert.
- Zutaten ausschließlich aus `Product` (Catalog) — kein Endpunkt für freie, selbst getippte
  Nährwerte; das ist eine bewusste Domänen-Grenze, kein technisches Detail.

## Tests (Abschnitt 9)

- Domain-Unit-Tests: `TotalGrams`/`TotalKcal`/`GramsPerPortion`/`NutrientsPer100`-Berechnung,
  `recipe-needs-ingredient` (leere Zutatenliste), `portions-invalid` (≤ 0).
- Value-Object-Tests (`RecipeName`, `Portions`).
- Integrationstest: `portions-to-diary` erzeugt tatsächlich einen `Diary`-Eintrag mit
  `EntrySource.FromRecipe` (End-to-End über M4 + M6).
- Integrationstests je Endpunkt inkl. Fehlerfälle, `curl`-Beispiele.
