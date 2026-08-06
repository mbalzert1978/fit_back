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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `shared_kernel/sync_batch/`: Batch-Konzepte (Operation-Union mit diary.addEntry/updateEntry/moveEntry/deleteEntry, Batch-Request/Response-Struktur); Invarianten: Reihenfolge muss erhalten bleiben, Fehler in einer Operation stoppen nicht die Verarbeitung, opId ist Idempotency-Key
- [ ] `shared_kernel/application/dispatch_batch/`: Dispatcher-Handler (ladet Operation um Operation, orchestriert den Aufruf des entsprechenden Use-Case-Handlers, sammelt Ergebnisse), Request-Mapper und Response-Mapper
- [ ] `shared_kernel/application/dispatch_batch/test_api.py` + `shared_kernel/application/dispatch_batch/fakes/` (In-Memory, Fake-Handler fuer jeden Operation-Typ)
- [ ] Verhaltens-Specs unter `shared_kernel/tests/dispatch_batch/`: Operationen werden in Sende-Reihenfolge verarbeitet (Reihenfolge-Test); eine fehlgeschlagene Operation enthaelt ein Fehler-Ergebnis im entsprechenden results-Eintrag, stoppt aber nicht die folgenden; opId zweimal ⇒ `status=duplicate` beim zweiten Mal
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container** — Handler sind gefakt
- [ ] `./make.ps1 import-lint` gruen, `slice-shape-check` liefert `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] Dispatcher-Handler integriert sich mit den echten Application-Services der verweigerten Diary-Use-Cases (addEntry, updateEntry, moveEntry, deleteEntry)
- [ ] Idempotency: opId-Duplikate werden ueber die M0.6-Idempotency-Middleware erkannt und liefern `status=duplicate` ohne neue Bearbeitung
- [ ] Integrationstest gegen Testcontainers-Postgres + echte Diary-Handler: je diary.*-Operation funktioniert korrekt im Batch-Kontext, Reihenfolge und Fehler-Toleranz sind garantiert

### Stufe 3 — HTTP

- [ ] `POST /api/v1/sync/batch` (neuer Endpunkt im shared API-Bereich oder als neuer Context) akzeptiert Batch-Request und verarbeitet Operationen ueber den Dispatcher
- [ ] Response enthielt je Operation einen results-Eintrag mit `opId`, `status` (applied/duplicate/failed), und bei Erfolg die Operation-spezifische Response-Payload
- [ ] End-to-End-Test mit gemischtem Batch verschiedener diary-Operationen; curl-Beispiel in der Ticket-Doku

## Blocked by

- Blocked by [0027](0027-m4-diaryday-diaryentry-aggregate-addentry-kopiersemantik-zusammenfassen.md)
- Blocked by [0029](0029-m4-updateentryamount-moveentry-deleteentry.md)
