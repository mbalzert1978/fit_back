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

- [ ] GET/POST/PATCH /api/v1/diary/slots... und PUT .../slots/order wie im Draft-Contract
- [ ] DELETE eines Slots mit Eintraegen liefert 409 slot-not-empty
- [ ] Domain-Unit-Tests je Invariante, Value-Object-Tests (SlotName, SlotPosition)
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
