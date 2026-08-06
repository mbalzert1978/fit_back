---
id: "0023"
title: M3: SearchProducts (Volltextsuche)
status: blocked
milestone: M3
type: AFK
---

# M3: SearchProducts (Volltextsuche)

## Parent

Meilenstein [M3](docs/milestones/m3-catalog-produkte.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

GET /api/v1/catalog/products?query=&take=&skip= - Volltext ueber Name und Brand (PostgreSQL tsvector, deutsche Konfiguration), eigene Produkte zuerst.

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/catalog/domain/`: Port fuer Volltext-Suche (mit Query-String, Limit/Offset, Nutzer-ID fuer Visibility-Prioritaet); SearchProductsError als TaggedUnion (falls vorhanden); Value Object SearchQuery (validiert Query-String); **nur stdlib**
- [ ] `contexts/catalog/application/search_products/`: Command (userId, query, take, skip als Primitive), Handler (orchestriert Query → Suche → Priorisierung, ~10-15 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit Such-Operation; **nur Primitive** ueber der Naht; eigene TaggedUnion als Naht-Ergebnis
- [ ] `application/search_products/test_api.py` + `application/search_products/fakes/` (In-Memory, mit einfacher In-Memory-Suche oder Mock-Treffer)
- [ ] Verhaltens-Specs unter `contexts/catalog/tests/search_products/`: Suche findet ueber Name und Brand, Groß-/Kleinschreibung egal, eigene private Produkte vor Public, Pagination (take/skip)
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, nutzt PostgreSQL `tsvector` mit deutscher Konfiguration fuer Name + Brand
- [ ] Alembic-Migration mit tsvector-Index auf `(name_tsv, brand_tsv)` oder generiertem GiST-Index
- [ ] Repository sorgt fuer Priorisierung: eigene private Produkte zuerst, dann Public
- [ ] Integrationstest gegen Testcontainers-Postgres mit echtem tsvector-Index: deutsche Wortformen (Plural), Priorisierung, Pagination

### Stufe 3 — HTTP

- [ ] `GET /api/v1/catalog/products?query=<string>&take=<int>&skip=<int>` liefert 200 mit items[] + total wie im Draft
- [ ] Suche findet Treffer ueber Name UND Brand, deutsche Wortformen (z.B. Plural) werden gefunden
- [ ] Eigene privaten Produkte erscheinen vor Public-Treffern
- [ ] End-to-End-Test; curl-Beispiel

## Blocked by

- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
