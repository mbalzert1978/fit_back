---
id: "0016"
title: M1: ChangePassword
status: blocked
milestone: M1
type: AFK
---

# M1: ChangePassword

## Parent

Meilenstein [M1](docs/milestones/m1-identity.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Use Case ChangePassword(current, new) - verifiziert das aktuelle Passwort und widerruft bei Erfolg alle Refresh-Tokens des Nutzers.

## Acceptance criteria

- [ ] POST /api/v1/identity/me/password liefert 204 bei korrektem current-Passwort
- [ ] 400 bei zu kurzem neuen Passwort, 401 bei falschem current-Passwort
- [ ] Alle bestehenden Refresh-Tokens des Nutzers sind danach nachweislich revoked
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0013](0013-m1-refreshtoken-aggregate-refreshsession-rotation-reuse-detection.md)
