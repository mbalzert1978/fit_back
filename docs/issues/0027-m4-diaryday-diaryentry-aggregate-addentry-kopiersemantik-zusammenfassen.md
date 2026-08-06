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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/diary/domain/`: DiaryDay-Aggregatwurzel (Schluessel UserId+DiaryDate) mit DiaryEntry als Child-Entity; Value Objects Grams, PortionLabel, EntrySource (Tagged Union: FromProduct/FromRecipe); Invarianten: Grams im Range, date <= heute+14 Tage, SourceId muss existieren (Validierung an Port-Grenze), Zusammenfassen-Regel (gleicher Slot + Tag + SourceId ⇒ Gramm addieren statt neue Zeile); **nur stdlib**
- [ ] Ein flacher, **context-eigener** `DiaryError` mit Fehlerfall je Invarianten-Verletzung (GramsOutOfRange, SlotNotFound, SourceNotFound, DateTooFarInFuture)
- [ ] `contexts/diary/application/add_diary_entry/`: Command (userId, date, slotId, sourceId, sourceType, grams, portionLabel), Handler (ladet oder erzeugt DiaryDay → prueft Invarianten → appliziert Zusammenfassen-Regel oder legt neue Entry an → gibt internes Outcome zurueck), Request-Mapper und Response-Mapper als **getrennte** Einheiten, Validierungsregeln
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` fuer MealSlot-Ladevorgang und Source-Validierung (Product/Recipe); **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/add_diary_entry/test_api.py` + `application/add_diary_entry/fakes/` (In-Memory, fake MealSlot- und Product-Gateway)
- [ ] Verhaltens-Specs unter `contexts/diary/specs/add_diary_entry/`: Entry erfolgreich anlegen (201), Zusammenfassen mit bestehendem Eintrag (200, addierte Gramm), Kopiersemantik (Produkt nach Erfassung aendern ⇒ Eintrag unveraendert), Out-of-Range-Gramm, unbekannter Slot/Source, Datum > 14 Tage in Zukunft
- [ ] Value-Object-Tests (Grams, PortionLabel); Tagged-Union-Serialisierungstest (EntrySource)
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, ladet DiaryDay per UserId+Date, persistiert Entries mit Zusammenfassen-Logik
- [ ] Alembic-Migration fuer `diary.diary_days` und `diary.diary_entries`
- [ ] Port-Adapter fuer MealSlot- und Product-Gateway, Anti-Corruption-Layer
- [ ] Integrationstest gegen Testcontainers-Postgres: Entry anlegen, Zusammenfassen, Kopiersemantik, Fehlerfall
- [ ] Idempotenz-Test (zweiter Aufruf mit gleichen Parametern und Idempotency-Key ⇒ 200, Eintrag unveraendert)

### Stufe 3 — HTTP

- [ ] `POST /api/v1/diary/days/{date}/entries` legt einen neuen Eintrag an (201) oder fasst ihn zusammen (200, addierte Gramm)
- [ ] Request-Schema: slotId, sourceType, sourceId, grams, portionLabel (optional)
- [ ] Response-Schema: id, date, slotId, source, grams, portionLabel, kcalPerGram, kcalTotal
- [ ] 400 `grams-out-of-range`
- [ ] 404 `meal-slot-not-found` / `source-not-found`
- [ ] 422 `date-too-far-in-future`
- [ ] Idempotency-Key-Header (M0.6) wird korrekt ausgewertet (zweiter Aufruf ⇒ 200)
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel

## Blocked by

- Blocked by [0025](0025-m4-mealslot-aggregate-slot-crud-reorder.md)
- Blocked by [0021](0021-m3-product-aggregate-nutrientsper100-createproductmanually.md)
