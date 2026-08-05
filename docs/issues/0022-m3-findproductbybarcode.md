---
id: "0022"
title: M3: FindProductByBarcode
status: blocked
milestone: M3
type: AFK
---

# M3: FindProductByBarcode

## Parent

Meilenstein [M3](docs/milestones/m3-catalog-produkte.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

GET /api/v1/catalog/products/by-barcode/{ean} - sucht zuerst in eigenen privaten Produkten des Nutzers, dann in Public.

## Acceptance criteria

- [ ] Treffer in eigenen privaten Produkten hat Vorrang vor Public
- [ ] 404 product-not-found ohne Treffer (kein technischer Fehler - Ausloeser fuer den Foto-Flow)
- [ ] 400 invalid-barcode bei falscher Pruefziffer
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
