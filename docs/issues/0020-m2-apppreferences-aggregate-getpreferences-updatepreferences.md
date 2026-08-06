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
- [ ] **Zwei getrennte Use Cases** — Abfrage und Kommando sind zwei Operationen, nie ein zusammengelegter Slice (siehe [`00-overview.md`](../milestones/00-overview.md), „Ein Ticket ist eine Liefereinheit, ein Use Case eine Code-Struktur"). Sie teilen sich die Domaene und den `DomainError` des Contexts, sonst nichts:
- [ ] `contexts/goals/application/get_preferences/`: Command (userId), Handler (orchestriert nur das Laden, ~5-10 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten
- [ ] `contexts/goals/application/update_preferences/`: Command (userId, neue Preferences), Handler (orchestriert Laden → Domaenen-Operation → Speichern, ~10-15 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten
- [ ] Public Naht **je Use Case**: eigenes, schmales `Protocol` mit **nur** den Operationen, die der jeweilige Use Case braucht (`get_preferences` liest, `update_preferences` liest und schreibt); **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] **Je Use Case eine eigene** `test_api.py` + `fakes/`: `application/get_preferences/` und `application/update_preferences/`
- [ ] Verhaltens-Specs unter `contexts/goals/specs/get_preferences/`: Preferences werden vollstaendig geliefert, Default-Werte fuer einen Nutzer ohne gespeicherte Preferences
- [ ] Verhaltens-Specs unter `contexts/goals/specs/update_preferences/`: Update erfolgreich, nur uebergebene Felder werden aktualisiert (Partial-Set)
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
