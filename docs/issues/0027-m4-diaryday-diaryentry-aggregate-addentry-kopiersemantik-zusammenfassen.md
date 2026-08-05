---
id: "0027"
title: M4: DiaryDay/DiaryEntry-Aggregate + AddEntry (Kopiersemantik, Zusammenfassen)
status: blocked
milestone: M4
type: AFK
---

# M4: DiaryDay/DiaryEntry-Aggregate + AddEntry (Kopiersemantik, Zusammenfassen)

## Parent

Meilenstein [M4](docs/milestones/m4-diary.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

DiaryDay-Aggregate (Schluessel UserId+DiaryDate) mit DiaryEntry als Child-Entity. AddEntry kopiert NutrientsPer100 aus der Quelle (Product ueber ProductId, vorerst nur EntrySource.FromProduct - FromRecipe existiert als Typ, bleibt bis M6 ungenutzt). Zusammenfassen-Regel: gleicher Slot + gleicher Tag + gleiche SourceId ⇒ Gramm addieren statt neue Zeile, Antwort 200 statt 201. Zukunft bis 14 Tage erlaubt.

## Acceptance criteria

- [ ] POST /api/v1/diary/days/{date}/entries legt einen neuen Eintrag an (201) oder fasst ihn mit einem bestehenden zusammen (200, addierte Gramm)
- [ ] Kopiersemantik-Test: Produkt nach Erfassung aendern ⇒ alter Eintrag unveraendert
- [ ] Zusammenfassen-Test: zweimal dasselbe Produkt in denselben Slot ⇒ ein Eintrag mit addierten Gramm
- [ ] 400 grams-out-of-range, 404 meal-slot-not-found/source-not-found, 422 date-too-far-in-future (> 14 Tage)
- [ ] Value-Object-Tests (Grams, PortionLabel), Tagged-Union-Serialisierungstest (EntrySource)
- [ ] Idempotenz-Test, Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0025](0025-m4-mealslot-aggregate-slot-crud-reorder.md)
- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
