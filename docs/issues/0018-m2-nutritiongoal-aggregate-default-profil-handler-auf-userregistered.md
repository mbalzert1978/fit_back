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

- [ ] Nach RegisterUser existiert fuer den neuen Nutzer automatisch ein NutritionGoal mit sinnvollen Default-Werten (End-to-End-Integrationstest ueber M1.1 + M2.1)
- [ ] EnergyFactors (Physiological 4.1/4.1/9.3, Declaration 4/4/9) und RoundingDirection (Up/Down mit eigenem Apply-Verhalten je Fall) sind als Tagged Unions modelliert und getestet
- [ ] Domain-Unit-Tests fuer alle Invarianten
- [ ] Contract-Test (siehe docs/milestones/02-test-pyramide.md, Form B): der Default-Profil-Handler wird gegen jedes kanonische UserRegistered-Beispiel aus contexts/identity/contracts/events/user_registered/examples/ ausgefuehrt (kein Testcontainers-Setup noetig) - ersetzt den bisher als 'End-to-End-Integrationstest ueber M1.1 + M2.1' formulierten Schnittstellenanteil

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
- Blocked by [0010](0010-m0-shared-kernel-postgres-outbox-event-relay-skip-locked-listen-notify.md)
