---
id: "0024"
title: M3: UpdateProduct (Owner-only, If-Match)
status: blocked
milestone: M3
type: AFK
---

# M3: UpdateProduct (Owner-only, If-Match)

## Parent

Meilenstein [M3](docs/milestones/m3-catalog-produkte.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

PUT /api/v1/catalog/products/{id} - nur durch den Besitzer eines privaten Produkts, mit Optimistic-Concurrency ueber If-Match (M0.7).

## Acceptance criteria

- [ ] 200 bei erfolgreichem Update durch den Owner
- [ ] 403 wenn ein anderer Nutzer versucht, ein fremdes privates Produkt zu aendern
- [ ] 409 concurrency-conflict bei veraltetem If-Match
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
