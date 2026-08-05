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

- [ ] Suche findet Treffer ueber Name UND Brand, deutsche Wortformen (z.B. Plural) werden gefunden
- [ ] Eigene privaten Produkte erscheinen vor Public-Treffern
- [ ] Response-Schema items[]/total wie im Draft
- [ ] Integrationstest gegen echten tsvector-Index, curl-Beispiel

## Blocked by

- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
