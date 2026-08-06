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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/identity/domain/`: UpdateProfileError als Tagged Union (InvalidTimeZone, InvalidLocale, o.ae.); Invarianten im User-Aggregat fuer Profilfeld-Updates (DisplayName, TimeZone, Locale duerfen unabhaengig aktualisiert werden)
- [ ] `contexts/identity/application/get_me/`: Command (userId), Handler (ladet User), Request-Mapper und Response-Mapper, public Naht mit Protocol, Response-DTO mit allen Feldern
- [ ] `contexts/identity/application/update_profile/`: Command (userId, displayName?, locale?, timeZoneId?), Handler (orchestriert nur), Request-Mapper und Response-Mapper als **getrennte** Einheiten, Validierungsregeln fuer UpdateProfile
- [ ] Public Naehte beider Use Cases: schmale Protokolle, **nur Primitive** ueber der Naht, je ein Response-Union-Typ
- [ ] `application/get_me/test_api.py` + `application/get_me/fakes/` (In-Memory); `application/update_profile/test_api.py` + `application/update_profile/fakes/` (In-Memory)
- [ ] Verhaltens-Specs: GetMe liefert alle Felder, UpdateProfile aktualisiert nur die uebergebenen Felder (Invarianten wie Locale/TimeZone), Lese-nach-Update-Konsistenz
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naehte aus Stufe 1, ladet/aktualisiert User
- [ ] Alembic-Migration fuer UpdateProfile-Felder (falls noch nicht von 0011 gedeckt)
- [ ] Integrationstests gegen Testcontainers-Postgres: Profilfeld-Updates, partielle Updates (nur ein Feld), Lese-nach-Update

### Stufe 3 — HTTP

- [ ] `GET /api/v1/identity/me` liefert 200 mit userId/email/displayName/locale/timeZoneId/createdUtc
- [ ] `PATCH /api/v1/identity/me` aktualisiert nur die uebergebenen Felder (displayName, locale, timeZoneId, je optional) und liefert 200 mit aktualisierten Feldern
- [ ] 400 bei ungueltigem Locale/TimeZoneId
- [ ] End-to-End-Tests; curl-Beispiele fuer beide Endpunkte

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
