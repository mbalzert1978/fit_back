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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/catalog/domain/`: Port fuer Barcode-Lookup (mit Nutzer-ID und Visibility-Logik: Prioritaet Private vor Public); FindProductError als TaggedUnion (NotFound, InvalidBarcode); **nur stdlib**
- [ ] `contexts/catalog/application/find_product_by_barcode/`: Command (userId, barcode als Primitive str), Handler (orchestriert Validierung → Lookup → Prioritaetssortierung, ~10-15 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit Operation zum Laden von Produkten nach Barcode/Visibility; **nur Primitive** ueber der Naht; eigene TaggedUnion als Naht-Ergebnis
- [ ] `application/find_product_by_barcode/test_api.py` + `application/find_product_by_barcode/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/catalog/specs/find_product_by_barcode/`: Treffer im eigenen privaten Produkt, Treffer nur in Public, kein Treffer (NotFound), falsche Pruefziffer (InvalidBarcode), Private hat Vorrang vor Public
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, ladet Produkte nach Barcode mit Visibility-Filter und sorgt fuer richtige Reihenfolge (Private zuerst)
- [ ] Integrationstest gegen Testcontainers-Postgres: Priorisierung, notFound-Fall, Barcode-Validierung

### Stufe 3 — HTTP

- [ ] `GET /api/v1/catalog/products/by-barcode/{ean}` liefert 200 mit dem Produkt
- [ ] 404 `product-not-found` ohne Treffer (kein technischer Fehler — Ausloeser fuer den Foto-Flow)
- [ ] 400 `invalid-barcode` bei falscher Pruefziffer
- [ ] End-to-End-Test; curl-Beispiel

## Blocked by

- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
