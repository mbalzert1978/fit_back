---
id: "0012"
title: M1: JWT-Auth-Pipeline + Login
status: blocked
milestone: M1
type: AFK
---

# M1: JWT-Auth-Pipeline + Login

## Parent

Meilenstein [M1](docs/milestones/m1-identity.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

JWT-Access-Token-Ausstellung (15 min) im Rahmen von Login(email, password), inkl. Argon2id-Verifikation. Auth-Middleware, die Bearer-JWT aus dem Authorization-Header liest und den angemeldeten UserId in den Request-Kontext einhaengt (Grundlage fuer IUserOwned aus M0.7).

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/identity/domain/`: PasswordHash-Value-Object und LoginError als Tagged Union (InvalidCredentials, AccountPendingDeletion); Domain-Port fuer Passwort-Verifikation
- [ ] `contexts/identity/application/login/`: Command (email, password), Handler (orchestriert nur, ~10-15 Zeilen, kein try/except), Request-Mapper und Response-Mapper als **getrennte** Einheiten, Validierungsregeln
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit **nur** den Operationen, die `login` braucht; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis (z.B. UserFound/UserNotFound/AccountDeletionPending)
- [ ] `application/login/test_api.py` + `application/login/fakes/` (In-Memory mit verschiedenen User-Stati)
- [ ] Verhaltens-Specs unter `contexts/identity/specs/login/`: erfolgreiche Anmeldung, falsch Passwort (identische Antwort wie unbekannte E-Mail), angemeldetes Konto mit PendingDeletion-Status
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, ladet User per Email
- [ ] Integrationstest gegen Testcontainers-Postgres (eigene, aeusserste Testebene — **nicht** Teil der Test-API)
- [ ] Auth-Middleware, die Bearer-JWT aus Authorization-Header liest und UserId in Request-Kontext einhaengt (Grundlage fuer IUserOwned aus M0.7)

### Stufe 3 — HTTP

- [ ] `POST /api/v1/identity/login` meldet den User an und liefert 200 mit userId/accessToken/refreshToken/expiresInSeconds
- [ ] 401 `invalid-credentials` bei falschem Passwort UND bei unbekannter E-Mail (identische Antwort — keine User-Enumeration)
- [ ] 403 `account-pending-deletion`, wenn Status PendingDeletion ist
- [ ] Ein geschuetzter Dummy-Endpunkt lehnt Anfragen ohne/mit ungueltigem Bearer-Token mit 401 ab
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel in der Ticket-Doku

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
