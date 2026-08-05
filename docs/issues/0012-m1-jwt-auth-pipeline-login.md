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

- [ ] POST /api/v1/identity/login liefert 200 mit userId/accessToken/refreshToken/expiresInSeconds
- [ ] 401 invalid-credentials bei falschem Passwort UND bei unbekannter E-Mail (identische Antwort - keine User-Enumeration)
- [ ] 403 account-pending-deletion, wenn Status PendingDeletion ist
- [ ] Ein geschuetzter Dummy-Endpunkt lehnt Anfragen ohne/mit ungueltigem Bearer-Token mit 401 ab
- [ ] Integrationstests inkl. Fehlerfaelle, curl-Beispiel

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
