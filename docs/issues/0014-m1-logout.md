---
id: "0014"
title: M1: Logout
status: blocked
milestone: M1
type: AFK
---

# M1: Logout

## Parent

Meilenstein [M1](docs/milestones/m1-identity.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Use Case Logout(refreshToken) - widerruft genau den uebergebenen Refresh-Token.

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/identity/domain/`: LogoutError als Tagged Union (TokenUnknown); Invariante im RefreshToken-Aggregat zur Revokation eines Tokens
- [ ] `contexts/identity/application/logout/`: Command (refreshToken als Primitive), Handler (orchestriert nur die Revokation, ~5-10 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit Operation zur Token-Revokation; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/logout/test_api.py` + `application/logout/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/identity/tests/logout/`: Token erfolgreich revoked, unbekannter Token
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, aktualisiert Token-Status
- [ ] Integrationstest gegen Testcontainers-Postgres: nach Logout ist der Token nicht mehr fuer RefreshSession nutzbar (401)

### Stufe 3 — HTTP

- [ ] `POST /api/v1/identity/logout` widerruft genau den uebergebenen Refresh-Token und liefert 204
- [ ] Der Token ist danach nachweislich nicht mehr fuer RefreshSession nutzbar (401)
- [ ] End-to-End-Test; curl-Beispiel

## Blocked by

- Blocked by [0012](0012-m1-jwt-auth-pipeline-login.md)
