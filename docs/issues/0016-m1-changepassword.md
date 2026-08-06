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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/identity/domain/`: ChangePasswordError als Tagged Union (InvalidCurrentPassword, InvalidNewPassword); Invarianten im User-Aggregat zur Passwort-Aenderung und zum Widerruf aller Tokens
- [ ] Domänenlogik: Nach erfolgreicher Passwort-Aenderung werden alle Refresh-Tokens des Nutzers revoked (Sicherheit)
- [ ] `contexts/identity/application/change_password/`: Command (userId, currentPassword, newPassword), Handler (orchestriert nur, Aggregat ladet → Passwort-Verifikation → Passwort aendert → Tokens revoked), Request-Mapper und Response-Mapper als **getrennte** Einheiten, Validierungsregeln
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit Operationen fuer Passwort-Verifikation und Token-Revokation; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/change_password/test_api.py` + `application/change_password/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/identity/specs/change_password/`: erfolgreiches Aendern, falsches current-Passwort, zu kurzes neues Passwort, erfolgreicher Token-Widerruf nach Aenderung
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1
- [ ] Integrationstest gegen Testcontainers-Postgres: nach Aenderung sind alle bestehenden Refresh-Tokens des Nutzers nachweislich revoked; Passwort-Aenderung ist transaktional mit Token-Revokation

### Stufe 3 — HTTP

- [ ] `POST /api/v1/identity/me/password` aendert das Passwort und liefert 204 bei korrektem current-Passwort
- [ ] 400 `invalid-new-password` bei zu kurzem neuem Passwort
- [ ] 401 `invalid-current-password` bei falschem current-Passwort
- [ ] End-to-End-Test; curl-Beispiel

## Blocked by

- Blocked by [0013](0013-m1-refreshtoken-aggregate-refreshsession-rotation-reuse-detection.md)
