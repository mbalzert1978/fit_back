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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/goals/domain/`: AppPreferences-Aggregatwurzel mit identitaetsbasierter Gleichheit; Value Objects Theme/Language/MeasurementSystem als geschlossene Tagged Unions; **nur stdlib**
- [ ] Ein flacher, **context-eigener** `DomainError` (TaggedUnion); Domain-Port zum Laden/Speichern
- [ ] `contexts/goals/application/get_and_update_preferences/`: Command (userId, neue Preferences), Handler (orchestriert nur, ~10-15 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit Laden/Speichern; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/get_and_update_preferences/test_api.py` + `application/get_and_update_preferences/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/goals/tests/get_and_update_preferences/`: Update erfolgreich, nur uebergebene Felder werden aktualisiert
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, persistiert AppPreferences
- [ ] Alembic-Migration fuer `goals.app_preferences`
- [ ] Integrationstest gegen Testcontainers-Postgres: Update mit Partial-Set, Serialisierungstests fuer Theme/Language/MeasurementSystem

### Stufe 3 — HTTP

- [ ] `GET /api/v1/preferences` liefert 200 mit theme/language/measurementSystem
- [ ] `PATCH /api/v1/preferences` aktualisiert nur uebergebene Felder und liefert 200
- [ ] Tagged-Union-Serialisierungstests in der HTTP-Ebene
- [ ] End-to-End-Test; curl-Beispiel

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
