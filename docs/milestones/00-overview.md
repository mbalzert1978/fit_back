# Meilensteine — Nährwert-Tracking-Backend

Abgeleitet aus [`docs/Draft/BACKEND.md`](../Draft/BACKEND.md), Abschnitt 8 „Reihenfolge der
Umsetzung", ergänzt um einen vorgezogenen Meilenstein 0 für das cross-cuttende Projekt-
Grundgerüst (ohne den Fehlerformat/Auth-Anteil aus Meilenstein 1 vorwegzunehmen, aber mit allem,
was *jeder* spätere Meilenstein technisch voraussetzt: Repo-Struktur, Docker-Compose, DB-Basis,
Shared Kernel).

Die fachliche Reihenfolge aus Abschnitt 8 bleibt unverändert; M0 ist rein technisch und liegt
davor, weil ohne ihn kein Context lauffähig wird.

## Technischer Rahmen dieser Portierung

Der Draft spezifiziert ASP.NET Core/C#. Dieses Repository ist ein Python-3.14-Projekt
(`pyproject.toml`, `.rules/python`); die fachlichen Regeln aus dem Draft werden 1:1 übernommen,
die technische Umsetzung erfolgt idiomatisch in Python nach `.rules/python/*`. Die dabei
getroffenen technischen Entscheidungen (Stack, Infrastruktur, Repo-Layout) stehen in
[`01-technical-decisions.md`](./01-technical-decisions.md) — dorthin verweisen alle Meilensteine
für Details, statt sie zu wiederholen.

## Meilenstein-Liste

| # | Titel | Bezug BACKEND.md | Voraussetzung |
|---|---|---|---|
| [M0](./m0-projekt-grundgeruest.md) | Projekt-Grundgerüst & Shared Kernel | Abschnitt 0 (Querschnitts-Regeln) | — |
| [M1](./m1-identity.md) | Identity & Access + Fehlerformat + Auth-Pipeline | Abschnitt 1, 8.1 | M0 |
| [M2](./m2-goals.md) | Goals & Preferences (Default-Profil) | Abschnitt 5, 8.2 | M1 |
| [M3](./m3-catalog-produkte.md) | Catalog: Produkt-Aggregat, Barcode-/Textsuche, manuelles Anlegen | Abschnitt 2 (ohne OCR), 8.3 | M1 |
| [M4](./m4-diary.md) | Diary: Slots, Tag, Einträge, Tagesaggregation | Abschnitt 3, 8.4 | M1, M2, M3 |
| [M5](./m5-catalog-ocr.md) | Catalog: Foto-Upload, OCR-Agent, Erfassung aus OCR | Abschnitt 2 (OCR-Teil), 8.5 | M3 |
| [M6](./m6-recipes.md) | Recipes | Abschnitt 4, 8.6 | M3, M4 |
| [M7](./m7-healthsync.md) | HealthSync | Abschnitt 6, 8.7 | M1, M4 |
| [M8](./m8-sync-batch.md) | Sync-Batch (Offline-Betrieb) | Abschnitt 7, 8.8 | M3, M4, M6, M7 |

## Querschnitts-Regeln (Abschnitt 0)

Die 13 Querschnitts-Regeln aus Abschnitt 0 des Drafts gelten **für jeden Meilenstein**, nicht nur
für M0. M0 baut die technischen Bausteine dafür (Idempotenz-Tabelle, Fehlerformat-Middleware,
`TimeProvider`-Äquivalent, Value-Object-Basis, Tagged-Union-Basis, Optimistic-Concurrency-Spalte);
jeder folgende Meilenstein wendet sie auf seine eigenen Aggregate an — das ist in jedem
Meilenstein-Dokument unter „Cross-Cutting-Check" explizit aufgeführt, damit es nicht stillschweigend
vergessen wird.

## Tests (Abschnitt 9)

Jeder Meilenstein liefert die in Abschnitt 9 geforderten Testarten für die von ihm eingeführten
Aggregate/Value Objects/Unions/Endpunkte mit (Domain-Unit-Tests, Value-Object-Tests,
Architekturtests, Union-Serialisierungstests, Rundungstests wo zutreffend, Idempotenz-Tests,
Integrationstests). Kein Meilenstein gilt als abgeschlossen, ohne dass diese Tests für seinen
Scope existieren und grün sind. Für die Kommunikation zwischen Bounded Contexts gilt zusätzlich
eine eigene Contract-Test-Ebene, siehe [`02-test-pyramide.md`](./02-test-pyramide.md).
