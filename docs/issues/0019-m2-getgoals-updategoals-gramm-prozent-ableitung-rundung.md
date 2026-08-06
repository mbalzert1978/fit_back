---
id: "0019"
title: M2: GetGoals + UpdateGoals (Gramm/Prozent-Ableitung, Rundung)
status: blocked
milestone: M2
type: AFK
---

# M2: GetGoals + UpdateGoals (Gramm/Prozent-Ableitung, Rundung)

## Parent

Meilenstein [M2](docs/milestones/m2-goals.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

GET/PUT /api/v1/goals mit der Gramm<->Prozent-Ableitung aus Abschnitt 5, inkl. der Konsistenzregel: Prozentsumme darf voruebergehend != 100 sein (kein 400), DailyKcal wird nur bei Summe == 100 aus den Gramm neu berechnet. Rundung ist hier implementiert und wird von M4 wiederverwendet.

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/goals/domain/`: Value Objects fuer MacroDistribution (Gramm ↔ Prozent), Rounding-Logik (EnergyFactors x RoundingDirection → apply-Methode je Fall); Invarianten (DailyKcal 800-8000, PercentSum voruebergehend != 100 erlaubt); **nur stdlib**
- [ ] Ein flacher, **context-eigener** `DomainError` (TaggedUnion, Fehler fuer Validierung); Domain-Port zum Laden/Speichern des Profils
- [ ] `contexts/goals/application/get_and_update_goals/`: Command (userId, neue MacroDistribution), Handler (orchestriert Laden → Validierung → Update, ~10-15 Zeilen), Request-Mapper und Response-Mapper als **getrennte** Einheiten, Validierungsregeln
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit Laden/Speichern; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/get_and_update_goals/test_api.py` + `application/get_and_update_goals/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/goals/tests/get_and_update_goals/`: Update erfolgreich, PercentSum != 100 aber kein Fehler, DailyKcal-out-of-range wird abgelehnt, Rundung Up/Down x Physiological/Declaration ueber bekannte Werte
- [ ] Assertion: berechnete Ausgaben haben nie Nachkommastellen
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen; `slice-shape-check` und `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, aktualisiert NutritionGoal
- [ ] Integrationstest gegen Testcontainers-Postgres: Update mit Rundung, PercentSum != 100
- [ ] Integrationtest mit Rundungstabelle: bekannte Testfaelle verifizieren

### Stufe 3 — HTTP

- [ ] `GET /api/v1/goals` liefert 200 mit dailyKcal, macros (percent/grams/kcal je Makro), percentSum, energyFactors, factors, roundingDirection, includeActivityInGoal exakt wie im Draft-Beispiel
- [ ] `PUT /api/v1/goals` mit PercentSum != 100 liefert 200 (kein Fehler), rechnet DailyKcal aber nicht neu
- [ ] 400 `daily-kcal-out-of-range` ausserhalb 800-8000
- [ ] End-to-End-Test; curl-Beispiel

## Blocked by

- Blocked by [0018](0018-m2-nutritiongoal-aggregate-default-profil-handler-auf-userregistered.md)
