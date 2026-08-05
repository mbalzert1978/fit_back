---
id: "0026"
title: M4: Standard-Slots-Outbox-Consumer auf UserRegistered
status: blocked
milestone: M4
type: AFK
---

# M4: Standard-Slots-Outbox-Consumer auf UserRegistered

## Parent

Meilenstein [M4](docs/milestones/m4-diary.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Outbox-Consumer, der auf UserRegistered (M1.1, ueber M0.10) reagiert und die drei Standard-Mahlzeiten-Slots anlegt: Fruehstueck, Mittagessen, Abendessen, in dieser Reihenfolge.

## Acceptance criteria

- [ ] Nach RegisterUser existieren fuer den neuen Nutzer automatisch genau drei Slots in exakt dieser Reihenfolge (End-to-End-Integrationstest ueber M1.1 + M4.1 + M4.2)
- [ ] Contract-Test (siehe docs/milestones/02-test-pyramide.md, Form B): der Standard-Slots-Handler wird gegen jedes kanonische UserRegistered-Beispiel aus contexts/identity/contracts/events/user_registered/examples/ ausgefuehrt (kein Testcontainers-Setup noetig)

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
- Blocked by [0025](0025-m4-mealslot-aggregate-slot-crud-reorder.md)
- Blocked by [0010](0010-m0-shared-kernel-postgres-outbox-event-relay-skip-locked-listen-notify.md)
