---
id: "0045"
title: M8: Sync-Batch health.putActivity
status: blocked
milestone: M8
type: AFK
---

# M8: Sync-Batch health.putActivity

## Parent

Meilenstein [M8](docs/milestones/m8-sync-batch.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Ergaenzt den Dispatcher aus M8.1/M8.2 um health.putActivity.

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `shared_kernel/sync_batch/`: Batch-Operation-Union um neuen Typ health.putActivity erweitert
- [ ] `shared_kernel/application/dispatch_batch/`: Dispatcher-Handler um Handhabung von health.putActivity erweitert; ruft den entsprechenden Application-Service des HealthSync-Contexts auf
- [ ] `shared_kernel/application/dispatch_batch/fakes/`: Fake-Handler fuer health.putActivity, damit Test-API unverhaendert bleibt
- [ ] Verhaltens-Specs unter `shared_kernel/tests/dispatch_batch/`: health.putActivity liefert im Batch denselben Effekt wie der Einzel-Endpunkt (Upsert je ExternalId); Ergebnis-Eintrag liefert `applied/duplicate/failed`
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container** — Handler ist gefakt

### Stufe 2 — Infrastruktur

- [ ] Dispatcher-Handler integriert sich mit dem echten Application-Service von HealthSync (put_activity)
- [ ] Idempotency: opId-Duplikate werden erkannt und liefern `status=duplicate`
- [ ] Integrationstest gegen Testcontainers-Postgres + echte HealthSync-Handler: health.putActivity funktioniert korrekt im Batch-Kontext, Upsert-Invariante ist erhalten

### Stufe 3 — HTTP

- [ ] `POST /api/v1/sync/batch`: health.putActivity wird akzeptiert und verarbeitet wie alle anderen Operationen
- [ ] Response liefert je Operation einen results-Eintrag mit `opId`, `status`, und bei Erfolg die Operation-spezifische Payload
- [ ] End-to-End-Test mit vollstaendigem Batch ueber alle 8 type-Werte (alle diary-, catalog-, recipes-, health-Operationen); curl-Beispiel in der Ticket-Doku

## Blocked by

- Blocked by [0043](0043-m8-sync-batch-dispatcher-grundgeruest-diary-operationen.md)
- Blocked by [0040](0040-m7-dailyactivity-aggregate-activity-endpunkte-upsert-je-externalid.md)
