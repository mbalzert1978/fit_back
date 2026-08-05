---
id: "0021"
title: M3: Product-Aggregate + NutrientsPer100 + CreateProductManually
status: blocked
milestone: M3
type: AFK
---

# M3: Product-Aggregate + NutrientsPer100 + CreateProductManually

## Parent

Meilenstein [M3](docs/milestones/m3-catalog-produkte.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Product-Aggregate (Barcode/Ean, Name, Brand, Nutrients, BasisUnit-Union, ProductOrigin-Union bereits vollstaendig als geschlossene Typhierarchie inkl. UserOcr-Fall, ProductVisibility-Union) und NutrientsPer100 mit allen Invarianten aus Abschnitt 2 (Pflichtfelder Kcal/Fat/Carbs/Protein, SaturatedFat<=Fat, Sugar<=Carbs, Fat+Carbs+Protein<=100). Use Case CreateProductManually.

## Acceptance criteria

- [ ] POST /api/v1/catalog/products (Origin=UserManual) liefert 201 mit dem angelegten Produkt
- [ ] 400 nutrients-invalid mit befuelltem errors-Objekt bei verletzten Invarianten
- [ ] 409 barcode-already-public bei doppeltem Barcode innerhalb Visibility=Public; private Produkte duerfen denselben Barcode tragen
- [ ] Domain-Unit-Tests je Invariante, Value-Object-Tests (Ean-Pruefziffer, ProductName, BrandName, NutrientAmount, Energy) + Architekturtest
- [ ] Tagged-Union-Serialisierungstests (BasisUnit, ProductOrigin, ProductVisibility)
- [ ] Idempotenz-Test, Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
