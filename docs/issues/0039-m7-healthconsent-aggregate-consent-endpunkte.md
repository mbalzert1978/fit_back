---
id: "0039"
title: M7: HealthConsent-Aggregate + Consent-Endpunkte
status: blocked
milestone: M7
type: AFK
---

# M7: HealthConsent-Aggregate + Consent-Endpunkte

## Parent

Meilenstein [M7](docs/milestones/m7-healthsync.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

HealthConsent-Aggregate (Connection-Union NotConnected/Connected, ImportActivity, ExportNutrition).

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/health_sync/domain/`: HealthConsent-Aggregatwurzel mit identitaetsbasierter Gleichheit; Connection als geschlossene Tagged Union (NotConnected/Connected mit Feldern ImportActivity/ExportNutrition), Value Objects fuer Flags; **nur stdlib**
- [ ] Ein flacher, **context-eigener** `HealthSyncDomainError` (Tagged Union, ein Fall je Fehlerursache)
- [ ] `contexts/health_sync/application/get_consent/`: Command (userId), Handler, Request-Mapper und Response-Mapper, Port-Adapter
- [ ] `contexts/health_sync/application/update_consent/`: Command (userId + teilweise gefuellte Felder), Handler, Request-Mapper und Response-Mapper, Validierungsregeln, Port-Adapter
- [ ] Public Naht: zwei eigene Protokolle (GetConsentGateway, UpdateConsentGateway), **nur Primitive** ueber der Naht; jeweils eigene Tagged Union als Naht-Ergebnis
- [ ] `application/get_consent/test_api.py` + `application/get_consent/fakes/` (In-Memory)
- [ ] `application/update_consent/test_api.py` + `application/update_consent/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/health_sync/specs/get_consent/` und `contexts/health_sync/specs/update_consent/`: GET liefert aktuellen Stand; PATCH mit teilweise gefuellten Feldern aktualisiert nur uebergebene Flags
- [ ] Tagged-Union-Serialisierungstest (Connection) unter `contexts/health_sync/specs/` (generischer Unit-Test)
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen, `slice-shape-check` liefert `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert beide Naehte aus Stufe 1; Alembic-Migration fuer `health_sync.consents`
- [ ] Integrationstest gegen Testcontainers-Postgres: GET und PATCH funktionieren korrekt gegen echte Persistenz

### Stufe 3 — HTTP

- [ ] `GET /api/v1/health/consent` liefert connected/importActivity/exportNutrition
- [ ] `PATCH /api/v1/health/consent` aktualisiert nur uebergebene Felder und liefert 200 mit aktuellem Stand
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel in der Ticket-Doku

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
