---
id: "0018"
title: M2: NutritionGoal-Aggregate + Default-Profil-Handler auf UserRegistered
status: blocked
milestone: M2
type: AFK
---

# M2: NutritionGoal-Aggregate + Default-Profil-Handler auf UserRegistered

## Parent

Meilenstein [M2](docs/milestones/m2-goals.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

NutritionGoal-Aggregate (DailyKcal, MacroDistribution, EnergyFactors-Union, RoundingDirection-Union, IncludeActivityInGoal) sowie ein Outbox-Consumer, der auf UserRegistered (M1.1) reagiert und ein Default-Zielprofil anlegt.

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/goals/domain/`: NutritionGoal-Aggregatwurzel mit identitaetsbasierter Gleichheit; Value Objects DailyKcal, MacroDistribution (Protein/Fat/Carbs-Gramm), EnergyFactors/RoundingDirection als geschlossene Tagged Unions; Invarianten (DailyKcal 800-8000, Makros > 0); **nur stdlib**
- [ ] Ein flacher, **context-eigener** `DomainError` (Tagged Union); Domain-Port fuer UserRegistered-Event-Konsum
- [ ] `contexts/goals/application/create_default_nutrition_goal/`: Command (userId), Handler (orchestriert nur, ~10-15 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` fuer Event-Konsum; **nur Primitive** ueber der Naht (userId als str); eigene Tagged Union als Naht-Ergebnis
- [ ] `application/create_default_nutrition_goal/test_api.py` + `application/create_default_nutrition_goal/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/goals/specs/create_default_nutrition_goal/`: erfolgreiche Erstellung eines Default-Profils, Invarianten validieren
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, persistiert NutritionGoal
- [ ] Alembic-Migration fuer `goals.nutrition_goals`
- [ ] Outbox-Consumer: bei Erhalt eines UserRegistered-Events wird das Default-Profil erstellt und in die Datenbank geschrieben
- [ ] Contract-Test (siehe [`02-test-pyramide.md`](../milestones/02-test-pyramide.md), Form B): der Default-Profil-Handler wird gegen jedes kanonische UserRegistered-Beispiel aus `contexts/identity/contracts/events/user_registered/examples/` ausgefuehrt
- [ ] Integrationstest gegen Testcontainers-Postgres: nach UserRegistered existiert das NutritionGoal

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
- Blocked by [0010](0010-m0-shared-kernel-postgres-outbox-event-relay-skip-locked-listen-notify.md) — **nur Stufe 2**; Stufe 1 ist davon unabhaengig
