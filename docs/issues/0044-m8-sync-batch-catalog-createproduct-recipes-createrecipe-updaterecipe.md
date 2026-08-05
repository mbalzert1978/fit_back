---
id: "0044"
title: M8: Sync-Batch catalog.createProduct + recipes.createRecipe/updateRecipe
status: blocked
milestone: M8
type: AFK
---

# M8: Sync-Batch catalog.createProduct + recipes.createRecipe/updateRecipe

## Parent

Meilenstein [M8](docs/milestones/m8-sync-batch.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Ergaenzt den Dispatcher aus M8.1 um catalog.createProduct, recipes.createRecipe und recipes.updateRecipe.

## Acceptance criteria

- [ ] Alle drei type-Werte liefern je einen applied/duplicate/failed-Ergebnis-Eintrag korrekt
- [ ] Integrationstest je Operation, curl-Beispiel

## Blocked by

- Blocked by [0043](0043-m8-sync-batch-dispatcher-grundgeruest-diary-operationen.md)
- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
- Blocked by [0035](0035-m6-recipe-recipeingredient-aggregate-createrecipe-normalisierung.md)
- Blocked by [0037](0037-m6-updaterecipe-zutaten-crud-deleterecipe.md)
