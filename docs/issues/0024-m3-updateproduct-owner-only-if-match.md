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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/catalog/domain/`: UpdateProductError als TaggedUnion (NotFound, NotOwner, ConcurrencyConflict); Invarianten im Product-Aggregat fuer Owner-Check und RowVersion (M0.7); **nur stdlib**
- [ ] `contexts/catalog/application/update_product/`: Command (productId, userId, neue Werte, rowVersion), Handler (orchestriert Laden → Owner-Check → RowVersion-Pruefung → Update, ~10-15 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit Load-/Save-Operation; **nur Primitive** ueber der Naht; eigene TaggedUnion als Naht-Ergebnis
- [ ] `application/update_product/test_api.py` + `application/update_product/fakes/` (In-Memory, mit einfacher Versionsverwaltung)
- [ ] Verhaltens-Specs unter `contexts/catalog/specs/update_product/`: erfolgreiches Update durch Owner, Ablehnung durch anderen Nutzer (NotOwner), Versionskonflikt bei veraltetem RowVersion
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, prueft Owner-ID, inkrementiert RowVersion, beruecksichtigt If-Match
- [ ] Alembic-Migration: RowVersion-Spalte fuer Products (M0.7)
- [ ] ProductUpdated landet **transaktional mit dem Update** in `shared.outbox`
- [ ] Integrationstest gegen Testcontainers-Postgres: erfolgreiches Update durch Owner, Versionskonflikt, fremder Nutzer wird abgelehnt

### Stufe 3 — HTTP

- [ ] `PUT /api/v1/catalog/products/{id}` mit If-Match-Header liefert 200 bei erfolgreichem Update durch den Owner
- [ ] 403 `forbidden` wenn ein anderer Nutzer versucht, ein fremdes privates Produkt zu aendern
- [ ] 409 `concurrency-conflict` bei veraltetem If-Match (RowVersion-Mismatch)
- [ ] End-to-End-Test; curl-Beispiel

## Blocked by

- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
