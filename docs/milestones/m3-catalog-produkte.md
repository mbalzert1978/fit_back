# M3 — Catalog: Produkt-Aggregat, Barcode-/Textsuche, manuelles Anlegen

**Bezug BACKEND.md:** Abschnitt 2 (ohne den OCR-Teil — der ist M5), Abschnitt 8.3.
**Voraussetzung:** M1 (Nutzeridentität für `Visibility.Private`/Mandantentrennung).

## Ziel

Produktstammdaten mit Nährwerten pro 100 g, Barcode-Suche, Textsuche, manuelles Anlegen. Trägt
das Kernversprechen der App — aber der Foto/OCR-Teil (Abschnitt 2, ab „NutritionPhoto") ist
bewusst nach M5 verschoben, damit dieser Meilenstein klein und für sich demonstrierbar bleibt
(„Barcode scannen → Produkt gefunden" funktioniert bereits ohne OCR).

## Scope

Aggregate: `Product` (ohne `Origin.UserOcr`-Fall bzw. mit ihm als Typ, aber ohne den Use Case, der
ihn erzeugt — der kommt in M5). `NutrientsPer100` als Value Object mit allen Invarianten
(Pflichtfelder, `SaturatedFat ≤ Fat`, `Sugar ≤ Carbs`, `Fat+Carbs+Protein ≤ 100`).

Use Cases: `FindProductByBarcode`, `SearchProducts`, `CreateProductManually`, `UpdateProduct`.

API: `GET /api/v1/catalog/products/by-barcode/{ean}`, `GET /api/v1/catalog/products`,
`POST /api/v1/catalog/products` (nur `Origin.UserManual`-Pfad), `PUT /api/v1/catalog/products/{id}`.

## Nicht in Scope

- `NutritionPhoto`-Aggregate, OCR-Agent, `POST /api/v1/catalog/photos`,
  `GET /api/v1/catalog/photos/{photoId}`, `CreateProductFromOcr` → **M5**.
- `Origin.UserOcr`/`ProductOrigin`-Union wird als **Typ** bereits vollständig modelliert (Abschnitt
  0.11 verlangt eine geschlossene Typhierarchie — die kann nicht nachträglich um einen Fall
  ergänzt werden, ohne alle bestehenden `match`-Stellen erneut anzufassen), aber der
  `UserOcr`-Fall bleibt bis M5 ungenutzt (kein Use Case erzeugt ihn).

## Tests (Abschnitt 9)

- Domain-Unit-Tests je Invariante von `Product`/`NutrientsPer100` (inkl. Barcode-Eindeutigkeit nur
  innerhalb `Visibility.Public`).
- Value-Object-Tests (`Ean`-Prüfziffer, `ProductName`, `BrandName`, `NutrientAmount`, `Energy`) +
  Architekturtest (kein rohes Primitive, kein `enum`).
- Tagged-Union-Serialisierungstests (`BasisUnit`, `ProductOrigin`, `ProductVisibility`).
- Volltextsuche: Integrationstest gegen `tsvector`/deutsche Konfiguration.
- Idempotenz-Test für `POST /products`.
- Integrationstests je Endpunkt inkl. Fehlerfälle (`product-not-found`, `invalid-barcode`,
  `nutrients-invalid`, `barcode-already-public`), zusätzlich `curl`-Beispiele gegen Docker Compose.
