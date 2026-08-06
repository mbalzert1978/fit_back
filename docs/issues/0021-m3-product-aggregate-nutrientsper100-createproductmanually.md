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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/catalog/domain/`: Product-Aggregatwurzel mit identitaetsbasierter Gleichheit; Value Objects Ean (mit Pruefziffer-Validierung per Factory), ProductName, BrandName, Energy (Kcal), NutrientAmount (Gramm per 100); Nutrients als VO mit Invarianten (Kcal/Fat/Carbs/Protein erforderlich, SaturatedFat<=Fat, Sugar<=Carbs, Fat+Carbs+Protein<=100); BasisUnit/ProductOrigin (mit UserManual-Fall)/ProductVisibility als geschlossene Tagged Unions; **nur stdlib**
- [ ] Ein flacher, **context-eigener** `DomainError` (TaggedUnion, ein Fall je Fehlerursache); Domain-Port zum Laden/Speichern von Produkten (mit Sichtbarkeitss-Check)
- [ ] `contexts/catalog/application/create_product_manually/`: Command (Nutzer-ID, Name, Brand, Ean, Nährstoffe), Handler (orchestriert Validierung → Aggregat erstellen → Repository speichern, ~10-15 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten, Validierungsregeln
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit Laden (mit Visibility-Parametern) und Speichern; **nur Primitive** ueber der Naht; eigene TaggedUnion als Naht-Ergebnis
- [ ] `application/create_product_manually/test_api.py` + `application/create_product_manually/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/catalog/specs/create_product_manually/`: erfolgreiches Anlegen, verletzter Nährstoff-Invarianten liefern Fehler, Ean-Pruefziffer-Validierung, Barcode-Duplikat nur innerhalb Visibility=Public wird abgelehnt
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, persistiert Product, beruecksichtigt Visibility-Check fuer Barcode-Duplikate
- [ ] Alembic-Migration fuer `catalog.products` mit Unique-Constraint auf (barcode, visibility) wo visibility='PUBLIC'
- [ ] ProductCreated landet **transaktional mit dem Insert** in `shared.outbox`
- [ ] Integrationstest gegen Testcontainers-Postgres: erfolgreiches Anlegen, Barcode-Duplikat-Check, Nährstoff-Invarianten
- [ ] Idempotenz-Test: zweite Anfrage mit demselben Ean liefert 200 mit demselben Produkt

### Stufe 3 — HTTP

- [ ] `POST /api/v1/catalog/products` (mit Origin=UserManual) liefert 201 mit dem angelegten Produkt (productId, Struktur wie im Draft)
- [ ] 400 `nutrients-invalid` mit befuelltem `errors`-Objekt bei verletzten Invarianten
- [ ] 409 `barcode-already-public` bei doppeltem Barcode innerhalb Visibility=Public; private Produkte duerfen denselben Barcode tragen
- [ ] End-to-End-Test; curl-Beispiel

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
