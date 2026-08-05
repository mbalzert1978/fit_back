---
id: "0029"
title: M4: UpdateEntryAmount / MoveEntry / DeleteEntry
status: blocked
milestone: M4
type: AFK
---

# M4: UpdateEntryAmount / MoveEntry / DeleteEntry

## Parent

Meilenstein [M4](docs/milestones/m4-diary.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

PATCH .../entries/{id} (Grams aendern), PATCH .../entries/{id}/slot (MealSlotId aendern, ggf. mit Zusammenfassen-Regel bei Kollision), DELETE .../entries/{id}.

## Acceptance criteria

- [ ] PATCH grams liefert 200 mit aktualisiertem Eintrag, 400 bei Out-of-Range, 404 bei unbekanntem Eintrag
- [ ] PATCH slot verschiebt den Eintrag und fasst ihn ggf. mit einem vorhandenen Eintrag im Ziel-Slot zusammen (dieselbe Zusammenfassen-Regel wie AddEntry)
- [ ] DELETE liefert 204 bzw. 404
- [ ] Integrationstests je Endpunkt, curl-Beispiele

## Blocked by

- Blocked by [0027](0027-m4-diaryday-diaryentry-aggregate-addentry-kopiersemantik-zusammenfassen.md)
