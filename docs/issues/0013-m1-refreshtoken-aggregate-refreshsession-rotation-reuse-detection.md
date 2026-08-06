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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/identity/domain/`: RefreshToken-Aggregatwurzel mit identitaetsbasierter Gleichheit; Value Objects (TokenHash, ExpiresAt); RefreshTokenStatus als Tagged Union (Active, Revoked); RefreshSessionError als Tagged Union (TokenExpired, TokenUnknown, TokenReused, AllTokensRevoked)
- [ ] Invarianten: Reuse-Detection — wenn ein revoked Token verwendet wird, **alle** Tokens des Nutzers werden revoked; Domain-Port fuer Token-Verifizierung
- [ ] `contexts/identity/application/refresh_session/`: Command (refreshToken als Primitive), Handler (orchestriert nur, ~10-15 Zeilen, kein try/except), Request-Mapper und Response-Mapper als **getrennte** Einheiten, Validierungsregeln
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit Operationen zum Laden und Rotieren von Tokens; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/refresh_session/test_api.py` + `application/refresh_session/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/identity/tests/refresh_session/`: erfolgreiche Rotation, abgelaufener Token, unbekannter Token, Reuse-Detection (revoked Token fuehrt zum Widerruf ALLER Tokens)
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1; Alembic-Migration fuer `identity.refresh_tokens` und `identity.refresh_sessions`
- [ ] RefreshTokenRotation bei erfolgreicher Verifikation: alter Token wird revoked, neuer Token generiert (transaktional)
- [ ] Reuse-Detection-Logik: wird ein revoked Token verwendet, alle Tokens des Nutzers werden revoked (transaktional)
- [ ] Integrationstest gegen Testcontainers-Postgres, inkl. Reuse-Detection-Fall

### Stufe 3 — HTTP

- [ ] `POST /api/v1/identity/refresh` liefert 200 mit neuen userId/accessToken/refreshToken/expiresInSeconds bei gueltigem Refresh-Token
- [ ] 401 `token-expired` bei abgelaufenem Token
- [ ] 401 `token-unknown` bei unbekanntem Token
- [ ] Wiederverwendung eines revoked Tokens liefert 401 mit deutlichem Fehler; nachweislich sind danach **alle** Refresh-Tokens des Nutzers revoked
- [ ] curl-Beispiel fuer den Reuse-Detection-Fall

## Blocked by

- Blocked by [0012](0012-m1-jwt-auth-pipeline-login.md)
