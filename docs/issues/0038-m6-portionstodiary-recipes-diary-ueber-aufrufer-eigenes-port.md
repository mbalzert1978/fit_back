---
id: "0038"
title: M6: PortionsToDiary (Recipes -> Diary ueber aufrufer-eigenes Port)
status: blocked
milestone: M6
type: AFK
---

# M6: PortionsToDiary (Recipes -> Diary ueber aufrufer-eigenes Port)

## Parent

Meilenstein [M6](docs/milestones/m6-recipes.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

POST /api/v1/recipes/{id}/portions-to-diary. Recipes definiert ein eigenes schmales DiaryGateway-Protocol (Anti-Corruption-Layer, siehe 'Cross-Context-Kommunikation' in 01-technical-decisions.md) und ruft darueber synchron Diary.AddEntry mit EntrySource.FromRecipe(RecipeId, Portions) auf - kein direkter Import von Diary-Domain/Handler-Code.

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/recipes/domain/`: (nutzt Recipe-Aggregat aus 0035)
- [ ] `contexts/recipes/application/ports/`: DiaryGateway-Protocol (Anti-Corruption-Layer), definiert **nur** die Operationen, die dieser Use Case braucht (z. B. add_entry_from_recipe); **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis (z. B. EntryAdded(entryId) | RecipeNotFound | MealSlotNotFound)
- [ ] `contexts/recipes/application/portions_to_diary/`: Command (recipeId, portions, mealSlotId), Handler (orchestriert nur), Request-Mapper, Response-Mapper
- [ ] `application/portions_to_diary/test_api.py` + `application/portions_to_diary/fakes/` (In-Memory DiaryGateway-Fake)
- [ ] Verhaltens-Specs unter `contexts/recipes/specs/portions_to_diary/`: Eintrag wird ueber DiaryGateway hinzugefuegt, unit=Portion|Gram wird korrekt verarbeitet, Fehlerfall RecipeNotFound/MealSlotNotFound
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1 (laedt Recipe)
- [ ] In-Process-Adapter implementiert DiaryGateway-Protocol, ruft ausschliesslich Diary's Application-Service auf (nicht dessen Domain/Handler/ORM)
- [ ] Integrationstest gegen Testcontainers-Postgres: Eintrag wird korrekkt angelegt (mit unit-Umrechnung in Gramm), bei fehlender Recipe/MealSlot wird Fehler gehoben
- [ ] **Contract-Test** (siehe `docs/milestones/02-test-pyramide.md`, Form A): Recipes definiert eine implementierungsunabhaengige Test-Suite `assert_diary_gateway_contract(gateway)` unter `contexts/recipes/specs/contracts/`, Diary importiert sie und fuehrt sie gegen seinen eigenen In-Process-Adapter aus

### Stufe 3 — HTTP

- [ ] `POST /api/v1/recipes/{id}/portions-to-diary` liefert 201 mit entryId
- [ ] unit=Portion|Gram wird korrekt in Gramm umgerechnet
- [ ] 404 `recipe-not-found` | `meal-slot-not-found`
- [ ] Der erzeugte Diary-Eintrag traegt EntrySource.FromRecipe mit korrekter RecipeId/Portions
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel

## Blocked by

- Blocked by [0035](0035-m6-recipe-recipeingredient-aggregate-createrecipe-normalisierung.md)
- Blocked by [0027](0027-m4-diaryday-diaryentry-aggregate-addentry-kopiersemantik-zusammenfassen.md)
