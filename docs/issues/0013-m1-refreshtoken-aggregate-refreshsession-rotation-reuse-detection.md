---
id: "0013"
title: M1: RefreshToken-Aggregate + RefreshSession (Rotation + Reuse-Detection)
status: blocked
milestone: M1
type: AFK
---

# M1: RefreshToken-Aggregate + RefreshSession (Rotation + Reuse-Detection)

## Parent

Meilenstein [M1](docs/milestones/m1-identity.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Eigenes RefreshToken-Aggregate (60 Tage Gueltigkeit). Bei Verwendung wird der alte Token revoked und ein neuer ausgegeben (Rotation). Wiederverwendung eines bereits revoked Tokens revoked alle Tokens des Nutzers und liefert 401.

## Acceptance criteria

- [ ] POST /api/v1/identity/refresh liefert 200 wie login bei gueltigem Refresh-Token
- [ ] 401 bei abgelaufenem/unbekanntem Token
- [ ] Wiederverwendung eines revoked Tokens fuehrt nachweislich zum Widerruf ALLER Refresh-Tokens des Nutzers (Domain-Unit-Test + Integrationstest)
- [ ] curl-Beispiel fuer den Reuse-Detection-Fall

## Blocked by

- Blocked by [0012](0012-m1-jwt-auth-pipeline-login.md)
