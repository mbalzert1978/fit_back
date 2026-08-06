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
- [ ] **Vier getrennte Use Cases** — jede Operation ist ein eigener Slice, nie ein zusammengelegter „manage"-Handler mit vier Commands (siehe [`00-overview.md`](../milestones/00-overview.md), „Ein Ticket ist eine Liefereinheit, ein Use Case eine Code-Struktur"). Sie teilen sich die Domaene und den `DiaryError` des Contexts, sonst nichts:
- [ ] `contexts/diary/application/create_meal_slot/`, `.../update_meal_slot/`, `.../delete_meal_slot/`, `.../reorder_meal_slots/` — je Ordner ein eigener Command, ein eigener Handler (orchestriert nur, ~5-15 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten, eigene Validierungsregeln
- [ ] Public Naht **je Use Case**: eigenes, schmales `Protocol` mit **nur** den Operationen, die der jeweilige Use Case braucht; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] **Je Use Case eine eigene** `test_api.py` + `fakes/`
- [ ] Verhaltens-Specs je Use Case unter `contexts/diary/specs/<use_case>/`: Slot anlegen; Slot aendern; Slot loeschen (ohne Eintraege erfolgreich, mit Eintraegen → Fehler, letzter verbleibender Slot → Fehler); Slots reordern (Position bleibt lueckenlos)
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
