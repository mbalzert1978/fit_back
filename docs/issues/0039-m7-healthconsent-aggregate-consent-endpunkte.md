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

- [ ] GET /api/v1/health/consent liefert connected/importActivity/exportNutrition
- [ ] PATCH aktualisiert nur uebergebene Felder
- [ ] Tagged-Union-Serialisierungstest (Connection)
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
