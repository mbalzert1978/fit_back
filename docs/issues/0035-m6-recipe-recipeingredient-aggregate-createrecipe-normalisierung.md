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

- [ ] POST /api/v1/recipes liefert 201 mit korrekt berechnetem totalGrams/gramsPerPortion/kcalPerPortion/nutrientsPer100
- [ ] 400 recipe-needs-ingredient bei leerer Zutatenliste, 400 portions-invalid bei portions<=0
- [ ] Domain-Unit-Tests der Berechnungsformeln, Value-Object-Tests (RecipeName, Portions)
- [ ] Idempotenz-Test, Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
