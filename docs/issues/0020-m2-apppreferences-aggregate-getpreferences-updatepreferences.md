---
id: "0020"
title: M2: AppPreferences-Aggregate + GetPreferences/UpdatePreferences
status: blocked
milestone: M2
type: AFK
---

# M2: AppPreferences-Aggregate + GetPreferences/UpdatePreferences

## Parent

Meilenstein [M2](docs/milestones/m2-goals.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

AppPreferences-Aggregate (Theme-Union Dark/Light, Language-Union, MeasurementSystem-Union) und die zugehoerigen Endpunkte.

## Acceptance criteria

- [ ] GET /api/v1/preferences liefert theme/language
- [ ] PATCH /api/v1/preferences aktualisiert nur uebergebene Felder
- [ ] Tagged-Union-Serialisierungstests fuer Theme/Language/MeasurementSystem
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
