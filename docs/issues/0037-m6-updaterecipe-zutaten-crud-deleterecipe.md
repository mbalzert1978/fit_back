---
id: "0037"
title: M6: UpdateRecipe + Zutaten-CRUD + DeleteRecipe
status: blocked
milestone: M6
type: AFK
---

# M6: UpdateRecipe + Zutaten-CRUD + DeleteRecipe

## Parent

Meilenstein [M6](docs/milestones/m6-recipes.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

PUT /api/v1/recipes/{id} (If-Match), AddIngredient/UpdateIngredientGrams/RemoveIngredient, DELETE /api/v1/recipes/{id}.

## Acceptance criteria

- [ ] PUT liefert 200 bei gueltigem If-Match, 409 bei veraltetem
- [ ] Zutaten-Aenderungen loesen die Normalisierung aus M6.1 erneut aus
- [ ] DELETE liefert 204
- [ ] Integrationstests je Endpunkt, curl-Beispiele

## Blocked by

- Blocked by [0035](0035-m6-recipe-recipeingredient-aggregate-createrecipe-normalisierung.md)
