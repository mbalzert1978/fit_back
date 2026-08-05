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

- [ ] health.putActivity liefert im Batch denselben Effekt wie der Einzel-Endpunkt (Upsert je ExternalId)
- [ ] Integrationstest, curl-Beispiel mit vollstaendigem Batch ueber alle 8 type-Werte

## Blocked by

- Blocked by [0043](0043-m8-sync-batch-dispatcher-grundgeruest-diary-operationen.md)
- Blocked by [0040](0040-m7-dailyactivity-aggregate-activity-endpunkte-upsert-je-externalid.md)
