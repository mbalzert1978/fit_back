---
id: "0043"
title: M8: Sync-Batch-Dispatcher-Grundgeruest + diary.*-Operationen
status: blocked
milestone: M8
type: AFK
---

# M8: Sync-Batch-Dispatcher-Grundgeruest + diary.*-Operationen

## Parent

Meilenstein [M8](docs/milestones/m8-sync-batch.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

POST /api/v1/sync/batch: operations werden in gesendeter Reihenfolge verarbeitet, eine fehlgeschlagene Operation stoppt die Verarbeitung nicht, opId ist zugleich Idempotency-Key. Dispatcher ruft je Operation denselben Application-Handler wie der jeweilige Einzel-Endpunkt auf (kein Duplikat der Fachlogik). Unterstuetzt in diesem Ticket: diary.addEntry/updateEntry/moveEntry/deleteEntry.

## Acceptance criteria

- [ ] Operationen werden strikt in Sende-Reihenfolge verarbeitet (Reihenfolge-Test)
- [ ] Eine fehlgeschlagene Operation liefert einen problem-Body (RFC 7807) im entsprechenden results-Eintrag, stoppt aber nicht die folgenden Operationen
- [ ] opId zweimal ⇒ status=duplicate beim zweiten Mal
- [ ] Integrationstest je diary.*-Operation, curl-Beispiel mit gemischtem Batch

## Blocked by

- Blocked by [0027](0027-m4-diaryday-diaryentry-aggregate-addentry-kopiersemantik-zusammenfassen.md)
- Blocked by [0029](0029-m4-updateentryamount-moveentry-deleteentry.md)
