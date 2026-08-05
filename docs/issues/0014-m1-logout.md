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

- [ ] POST /api/v1/identity/logout liefert 204 und der Token ist danach nicht mehr fuer RefreshSession nutzbar (401)
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0012](0012-m1-jwt-auth-pipeline-login.md)
