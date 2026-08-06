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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/recipes/domain/`: (nutzt Recipe-Aggregat aus 0035 mit seinen Methoden fuer Ingredient-CRUD)
- [ ] `contexts/recipes/application/update_recipe/`: Command (recipeId, name?, portions?, rowVersion), Handler, Request-Mapper, Response-Mapper, Validierungsregeln
- [ ] `contexts/recipes/application/add_ingredient/`: Command (recipeId, productId, grams), Handler, Request-Mapper, Response-Mapper
- [ ] `contexts/recipes/application/update_ingredient_grams/`: Command (recipeId, ingredientId, grams), Handler, Request-Mapper, Response-Mapper
- [ ] `contexts/recipes/application/remove_ingredient/`: Command (recipeId, ingredientId), Handler, Request-Mapper, Response-Mapper
- [ ] `contexts/recipes/application/delete_recipe/`: Command (recipeId, rowVersion), Handler, Request-Mapper, Response-Mapper
- [ ] Test-APIs + Fakes fuer alle Operationen
- [ ] Verhaltens-Specs unter `contexts/recipes/tests/`: Rezept wird aktualisiert, Zutaten-Aenderungen loesen Normalisierung aus, RowVersion-Konflikt wird erkannt, Rezept wird geloescht
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert Ingredient-CRUD und Update + Delete mit RowVersion-Optimistic-Locking
- [ ] Integrationstest gegen Testcontainers-Postgres: alle CRUD-Operationen funktionieren, Normalisierung wird erneut berechnet, RowVersion-Konflikt wird erkannt

### Stufe 3 — HTTP

- [ ] `PUT /api/v1/recipes/{id}` (If-Match fuer RowVersion) liefert 200 bei gueltigem If-Match, 409 bei veraltetem
- [ ] `POST /api/v1/recipes/{id}/ingredients` fuegt Zutat hinzu (AddIngredient)
- [ ] `PUT /api/v1/recipes/{id}/ingredients/{ingredientId}` aendert Grams (UpdateIngredientGrams)
- [ ] `DELETE /api/v1/recipes/{id}/ingredients/{ingredientId}` entfernt Zutat (RemoveIngredient)
- [ ] `DELETE /api/v1/recipes/{id}` liefert 204
- [ ] Zutaten-Aenderungen loesen die Normalisierung aus M6.1 erneut aus
- [ ] Integrationstests je Endpunkt; curl-Beispiele

## Blocked by

- Blocked by [0035](0035-m6-recipe-recipeingredient-aggregate-createrecipe-normalisierung.md)
