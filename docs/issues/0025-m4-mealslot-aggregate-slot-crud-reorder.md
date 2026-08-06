---
id: "0025"
title: M4: MealSlot-Aggregate + Slot-CRUD/Reorder
status: blocked
milestone: M4
type: AFK
---

# M4: MealSlot-Aggregate + Slot-CRUD/Reorder

## Parent

Meilenstein [M4](docs/milestones/m4-diary.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

MealSlot-Aggregate (Name, Position, IsArchived) mit den Invarianten: mindestens ein Slot pro Nutzer, Position lueckenlos, Loeschen eines Slots mit Eintraegen nicht erlaubt.

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/diary/domain/`: MealSlot-Aggregatwurzel mit Value Objects (SlotName, SlotPosition, IsArchived); Invarianten: mindestens ein Slot pro Nutzer, Position lueckenlos, Löschen eines Slots mit Eintraegen nicht erlaubt; **nur stdlib**
- [ ] Ein flacher, **context-eigener** `DiaryError` (Tagged Union) mit Fehlerfall je Invarianten-Verletzung; Domain-Ports als `Protocol`
- [ ] `contexts/diary/application/manage_meal_slots/`: Commands (CreateMealSlot, UpdateMealSlot, DeleteMealSlot, ReorderMealSlots), Handler (orchestriert nur, ~15-20 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten, Validierungsregeln
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit Operationen zur Slot-Verwaltung; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/manage_meal_slots/test_api.py` + `application/manage_meal_slots/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/diary/tests/manage_meal_slots/`: Slot anlegen, Slot aendern, Slot loeschen (ohne Eintraege erfolgreich, mit Eintraegen → Fehler), Slots reordern, mindestens ein Slot bleibt erhalten
- [ ] Value-Object-Tests (SlotName, SlotPosition); Invarianten-Tests
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1
- [ ] Alembic-Migration fuer `diary.meal_slots`
- [ ] Integrationstest gegen Testcontainers-Postgres: Slots persistiert, Reorder, Loeschen mit Eintraegen schlaegt fehl

### Stufe 3 — HTTP

- [ ] `GET /api/v1/diary/slots` liefert alle Slots des Nutzers in Reihenfolge
- [ ] `POST /api/v1/diary/slots` legt einen neuen Slot an (201)
- [ ] `PATCH /api/v1/diary/slots/{slotId}` aendert Slot-Name oder Position
- [ ] `PUT /api/v1/diary/slots/order` nimmt array of {slotId, position} und reordert
- [ ] `DELETE /api/v1/diary/slots/{slotId}` loescht den Slot (204) oder liefert 409 `slot-not-empty` wenn Eintraege existieren
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiele

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
