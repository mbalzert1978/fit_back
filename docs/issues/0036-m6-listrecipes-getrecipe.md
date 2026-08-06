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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/recipes/domain/`: (keine neue Domain; nutzt Recipe-Aggregat aus 0035)
- [ ] `contexts/recipes/application/list_recipes/`: Command (sortMode: name_asc|name_desc|recent), Handler, Response-Mapper
- [ ] `contexts/recipes/application/get_recipe/`: Command (recipeId), Handler, Response-Mapper
- [ ] Response-DTOs enthalten ingredients[] mit id/productId/displayName/grams/nutrientsPer100/computedKcal
- [ ] `application/list_recipes/test_api.py` + `application/list_recipes/fakes/`; `application/get_recipe/test_api.py` + `application/get_recipe/fakes/`
- [ ] Verhaltens-Specs unter `contexts/recipes/specs/list_recipes/` und `contexts/recipes/specs/get_recipe/`: Sortierung nach allen drei Modi, GetRecipe liefert Zutaten mit berechneten Kcal
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Queries implementieren Sortierung (name_asc, name_desc, recent by created_at) und Zutaten-Laden mit Product-Joins
- [ ] Integrationstest gegen Testcontainers-Postgres: alle drei Sortierungen funktionieren, GetRecipe enthaelt korrekte Zutaten-Daten

### Stufe 3 — HTTP

- [ ] `GET /api/v1/recipes?sort=name_asc|name_desc|recent` liefert sortierte Liste mit Rezeptdaten
- [ ] `GET /api/v1/recipes/{id}` liefert einzelnes Rezept inkl. ingredients[] mit computedKcal
- [ ] Sortierung nach allen drei Modi korrekt
- [ ] End-to-End-Tests gegen die laufende App; curl-Beispiele

## Blocked by

- Blocked by [0035](0035-m6-recipe-recipeingredient-aggregate-createrecipe-normalisierung.md)
