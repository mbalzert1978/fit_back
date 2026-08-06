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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `shared_kernel/sync_batch/`: Batch-Operation-Union um drei neue Typen erweitert (catalog.createProduct, recipes.createRecipe, recipes.updateRecipe)
- [ ] `shared_kernel/application/dispatch_batch/`: Dispatcher-Handler um Handhabung der drei neuen Operationen erweitert; ruft die entsprechenden Application-Services der Catalog- und Recipes-Contexts auf
- [ ] `shared_kernel/application/dispatch_batch/fakes/`: Fake-Handler fuer die neuen Operationen, damit Test-API unverhaendert bleibt
- [ ] Verhaltens-Specs unter `shared_kernel/tests/dispatch_batch/`: Alle drei type-Werte liefern je einen `applied/duplicate/failed`-Ergebnis-Eintrag korrekt; Fachlogik (Validierung, Duplikat-Erkennung) wird an die echten Handler delegiert
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container** — Handler sind gefakt

### Stufe 2 — Infrastruktur

- [ ] Dispatcher-Handler integriert sich mit den echten Application-Services von Catalog und Recipes (createProduct, createRecipe, updateRecipe)
- [ ] Idempotency: opId-Duplikate werden erkannt und liefern `status=duplicate`
- [ ] Integrationstest gegen Testcontainers-Postgres + echte Handler: je Operation funktioniert korrekt im Batch-Kontext

### Stufe 3 — HTTP

- [ ] `POST /api/v1/sync/batch`: Die drei neuen type-Werte werden vom Endpunkt akzeptiert und verarbeitet
- [ ] Response liefert je Operation einen results-Eintrag mit `opId`, `status` (applied/duplicate/failed), und bei Erfolg die Operation-spezifische Response-Payload
- [ ] End-to-End-Test mit gemischtem Batch verschiedener Operationen; curl-Beispiel mit catalog/recipes-Operationen in der Ticket-Doku

## Blocked by

- Blocked by [0043](0043-m8-sync-batch-dispatcher-grundgeruest-diary-operationen.md)
- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
- Blocked by [0035](0035-m6-recipe-recipeingredient-aggregate-createrecipe-normalisierung.md)
- Blocked by [0037](0037-m6-updaterecipe-zutaten-crud-deleterecipe.md)
