---
id: "0035"
title: M6: Recipe/RecipeIngredient-Aggregate + CreateRecipe (Normalisierung)
status: blocked
milestone: M6
type: AFK
---

# M6: Recipe/RecipeIngredient-Aggregate + CreateRecipe (Normalisierung)

## Parent

Meilenstein [M6](docs/milestones/m6-recipes.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Recipe-Aggregate mit RecipeIngredient-Entities (Zutaten ausschliesslich aus Product/ProductId - kein Endpunkt fuer freie Zutaten). Beim Speichern Normalisierung auf NutrientsPer100 (TotalGrams/TotalKcal/GramsPerPortion/NutrientsPer100-Berechnung aus Abschnitt 4).

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/recipes/domain/`: Recipe-Aggregatwurzel mit identitaetsbasierter Gleichheit; RecipeIngredient-Entities (ProductId, Grams); RecipeName/Portions als Value Objects; Normalisierung-Logik (TotalGrams/GramsPerPortion/NutrientsPer100 aus BACKEND.md Abschnitt 4); **nur stdlib**
- [ ] Domain-Error als Tagged Union (RecipeNeedsIngredient, PortionsInvalid, ProductNotFound, etc.); Domain-Ports
- [ ] `contexts/recipes/application/create_recipe/`: Command (name, portions, ingredients[]), Handler (orchestriert nur), Request-Mapper und Response-Mapper als **getrennte** Einheiten, Validierungsregeln
- [ ] Public Naht des Use Case: Protocol fuer Product-Ladevorgang (um Nutrient-Daten zu beziehen); **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/create_recipe/test_api.py` + `application/create_recipe/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/recipes/tests/create_recipe/`: Rezept mit Normalisierung (Berechnung totalGrams, gramsPerPortion, nutrientsPer100), leere Zutatenliste wird abgelehnt, portions<=0 wird abgelehnt
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] Domain-Unit-Tests der Berechnungsformeln, Value-Object-Tests (RecipeName, Portions)
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1; Alembic-Migration fuer `recipes.recipes` und `recipes.recipe_ingredients`
- [ ] Integrationstest gegen Testcontainers-Postgres: Rezept mit Normalisierung wird gespeichert, Zutaten-Beziehung zu Products funktioniert

### Stufe 3 — HTTP

- [ ] `POST /api/v1/recipes` liefert 201 mit korrekt berechnetem totalGrams/gramsPerPortion/kcalPerPortion/nutrientsPer100
- [ ] 400 `recipe-needs-ingredient` bei leerer Zutatenliste, 400 `portions-invalid` bei portions<=0
- [ ] Idempotency-Key-Header wird ueber die M0.6-Middleware ausgewertet
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel

## Blocked by

- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
