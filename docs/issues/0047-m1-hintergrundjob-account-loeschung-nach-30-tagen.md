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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/identity/domain/`: DeleteExpiredUserError als Tagged Union (UserNotFound, UserNotPendingDeletion); Invarianten im User-Aggregat fuer Loeschung: nur PendingDeletion-Nutzer duerfen geloescht werden, EffectiveAt muss in der Vergangenheit liegen
- [ ] `contexts/identity/application/delete_expired_user/`: Command (userId), Handler (orchestriert nur, ladet User → prueft EffectiveAt-Bedingung → loescht), Request-Mapper und Response-Mapper, Validierungsregeln
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` fuer Nutzer-Ladevorgang und Status-Pruefung; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/delete_expired_user/test_api.py` + `application/delete_expired_user/fakes/` (In-Memory, Fake-TimeProvider)
- [ ] Verhaltens-Specs unter `contexts/identity/tests/delete_expired_user/`: Nutzer mit EffectiveAt in der Vergangenheit wird geloescht, Nutzer mit EffectiveAt in der Zukunft bleibt unangetastet, nur PendingDeletion-Status wird geloescht
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container** — verwendet gefakete Zeit (TimeProvider aus M0.4)

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, ladet Nutzer mit PendingDeletion-Status, loescht User-Aggregat
- [ ] Job-Scheduler/Hintergrundjob: Periodisch (z.B. stundlich) werden Nutzer mit `EffectiveAt <= now()` geladen und geloescht
- [ ] `UserDeleted` landet **transaktional mit der Loeschung** in `shared.outbox` (M0.10)
- [ ] Integrationstest gegen Testcontainers-Postgres mit gefaketer Zeit (TimeProvider): Nutzer mit abgelaufenem EffectiveAt wird geloescht und Event ist in Outbox; Nutzer mit zukuenftigem EffectiveAt bleibt unangetastet

## Blocked by

- Blocked by [0017](0017-m1-requestaccountdeletion-userdeletionrequested-userdeleted-outbox-events.md)
