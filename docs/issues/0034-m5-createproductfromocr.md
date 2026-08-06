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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/catalog/domain/`: Product-Aggregat (bereits aus 0021) traegt Origin-Union mit UserOcr(PhotoId) Variante; **nur stdlib**
- [ ] Domain-Error nutzt die bereits vorhandene Product-DomainError (keine neue Fehlerart)
- [ ] `contexts/catalog/application/create_product_from_ocr/`: Command (name, barcode?, nutrients, sourcePhotoId), Handler (orchestriert nur), Request-Mapper und Response-Mapper als **getrennte** Einheiten, Validierungsregeln
- [ ] Public Naht des Use Case: Protocol fuer Photo-Ladevorgang und ggf. Product-Repository; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/create_product_from_ocr/test_api.py` + `application/create_product_from_ocr/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/catalog/specs/create_product_from_ocr/`: Produkt wird mit Origin.UserOcr(photoId) angelegt, Nutrients-Invarianten aus 0021 greifen
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1 (nutzt bestehende Product-Repository)
- [ ] Integrationstest gegen Testcontainers-Postgres: Produkt wird mit korrekter PhotoId gespeichert

### Stufe 3 — HTTP

- [ ] `POST /api/v1/catalog/products` mit befuelltem sourcePhotoId liefert 201 mit dem angelegten Produkt
- [ ] Origin ist UserOcr mit korrekter PhotoId
- [ ] Dieselben Nutrients-Invarianten wie bei CreateProductManually greifen (Wiederverwendung von M3.1)
- [ ] End-to-End-Integrationstest (Upload -> Polling -> CreateProductFromOcr); curl-Beispiel

## Blocked by

- Blocked by [0033](0033-m5-getphotoresult-polling.md)
- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
