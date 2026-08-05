---
id: "0047"
title: "M1: Hintergrundjob Account-Loeschung nach 30 Tagen"
status: blocked
milestone: M1
type: AFK
---

# M1: Hintergrundjob Account-Loeschung nach 30 Tagen

## Parent

Meilenstein [M1](../milestones/m1-identity.md) - siehe dort fuer vollstaendigen fachlichen
Kontext und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Hintergrundjob, der Nutzer mit Status `PendingDeletion(EffectiveAt)` nach Erreichen von
`EffectiveAt` tatsaechlich loescht (Abschnitt 1: "Loeschung nach 30 Tagen per Hintergrundjob") und
`UserDeleted` ueber die Postgres-Outbox (M0.10) publiziert, worauf jeder andere Context (M2, M3,
M4, M6, M7) unabhaengig seine eigenen Nutzerdaten loescht.

## Acceptance criteria

- [ ] Ein Nutzer mit `EffectiveAt` in der Vergangenheit wird vom Job geloescht (User-Aggregate
      entfernt)
- [ ] Ein Nutzer mit `EffectiveAt` in der Zukunft bleibt unangetastet
- [ ] `UserDeleted` landet transaktional mit der Loeschung in `shared.outbox`
- [ ] Integrationstest mit gefaketer Zeit (TimeProvider aus M0.4)

## Blocked by

- Blocked by [0017](0017-m1-requestaccountdeletion-userdeletionrequested-userdeleted-outbox-events.md)
