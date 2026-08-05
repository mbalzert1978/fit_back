---
id: "0036"
title: M6: ListRecipes + GetRecipe
status: blocked
milestone: M6
type: AFK
---

# M6: ListRecipes + GetRecipe

## Parent

Meilenstein [M6](docs/milestones/m6-recipes.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

GET /api/v1/recipes?sort= (name_asc/name_desc/recent) und GET /api/v1/recipes/{id} inkl. Zutatenliste mit computedKcal je Zutat.

## Acceptance criteria

- [ ] Sortierung nach allen drei Modi korrekt
- [ ] GetRecipe liefert ingredients[] mit id/productId/displayName/grams/nutrientsPer100/computedKcal
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0035](0035-m6-recipe-recipeingredient-aggregate-createrecipe-normalisierung.md)
