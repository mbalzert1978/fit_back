---
id: "0015"
title: M1: GetMe + UpdateProfile
status: blocked
milestone: M1
type: AFK
---

# M1: GetMe + UpdateProfile

## Parent

Meilenstein [M1](docs/milestones/m1-identity.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

GET /api/v1/identity/me liefert die Profildaten des angemeldeten Nutzers, PATCH aktualisiert displayName/locale/timeZoneId (jeweils optional).

## Acceptance criteria

- [ ] GET /me liefert userId/email/displayName/locale/timeZoneId/createdUtc
- [ ] PATCH /me aktualisiert nur die uebergebenen Felder und liefert 200 wie GET
- [ ] Domain-Unit-Test fuer UpdateProfile-Invarianten, Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
