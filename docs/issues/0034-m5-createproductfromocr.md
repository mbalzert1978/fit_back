---
id: "0034"
title: M5: CreateProductFromOcr
status: blocked
milestone: M5
type: AFK
---

# M5: CreateProductFromOcr

## Parent

Meilenstein [M5](docs/milestones/m5-catalog-ocr.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

POST /api/v1/catalog/products mit befuelltem sourcePhotoId - legt Product mit Origin=UserOcr(PhotoId), VerifiedByUser=true an, nachdem der Nutzer die OCR-Werte bestaetigt oder korrigiert hat.

## Acceptance criteria

- [ ] 201 mit dem angelegten Produkt, Origin ist UserOcr mit korrekter PhotoId
- [ ] Dieselben Nutrients-Invarianten wie bei CreateProductManually greifen (Wiederverwendung von M3.1)
- [ ] Integrationstest End-to-End (Upload -> Polling -> CreateProductFromOcr), curl-Beispiel

## Blocked by

- Blocked by [0033](0033-m5-getphotoresult-polling.md)
- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
