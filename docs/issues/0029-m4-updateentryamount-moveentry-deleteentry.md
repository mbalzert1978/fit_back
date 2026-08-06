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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/diary/domain/`: Invarianten im DiaryEntry + DiaryDay fuer die Operationen UpdateAmount (Grams im Range), MoveEntry (neuer Slot muss existieren, Zusammenfassen-Regel applizieren), DeleteEntry (alles ok)
- [ ] `contexts/diary/application/update_entry_amount/`: Command (entryId, newGrams), Handler, Request-Mapper, Response-Mapper, Validierungsregeln
- [ ] `contexts/diary/application/move_entry/`: Command (entryId, newSlotId), Handler, Request-Mapper, Response-Mapper, Validierungsregeln (appliziert Zusammenfassen-Regel)
- [ ] `contexts/diary/application/delete_entry/`: Command (entryId), Handler, Request-Mapper, Response-Mapper
- [ ] Public Nähte: je Anwendungsfall eigene schmale Protocols; **nur Primitive** ueber der Naht
- [ ] `application/update_entry_amount/test_api.py` + fakes, `application/move_entry/test_api.py` + fakes, `application/delete_entry/test_api.py` + fakes
- [ ] Verhaltens-Specs: UpdateAmount (200 ok, 400 out-of-range, 404 not-found), MoveEntry (200 ok, 404 slot not-found, Zusammenfassen-Regel wird appliziert), DeleteEntry (204 ok, 404 not-found)
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naehte fuer alle drei Operationen
- [ ] Integrationstest gegen Testcontainers-Postgres je Endpunkt: Grams aendern, Entry verschieben mit/ohne Zusammenfassen, Entry loeschen

### Stufe 3 — HTTP

- [ ] `PATCH /api/v1/diary/days/{date}/entries/{entryId}` (Grams aendern) liefert 200 mit aktualisiertem Eintrag, 400 bei `grams-out-of-range`, 404 bei unbekanntem Eintrag
- [ ] `PATCH /api/v1/diary/days/{date}/entries/{entryId}/slot` (MealSlotId aendern) liefert 200, verschiebt den Eintrag und fasst ihn ggf. mit einem vorhandenen Eintrag im Ziel-Slot zusammen (dieselbe Zusammenfassen-Regel wie AddEntry), 404 wenn Slot nicht existiert
- [ ] `DELETE /api/v1/diary/days/{date}/entries/{entryId}` liefert 204 bzw. 404
- [ ] End-to-End-Tests gegen die laufende App; curl-Beispiele je Endpunkt

## Blocked by

- Blocked by [0027](0027-m4-diaryday-diaryentry-aggregate-addentry-kopiersemantik-zusammenfassen.md)
