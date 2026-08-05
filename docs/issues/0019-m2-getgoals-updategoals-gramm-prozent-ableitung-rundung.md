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

- [ ] GET /goals liefert dailyKcal, macros (percent/grams/kcal je Makro), percentSum, energyFactors, factors, roundingDirection, includeActivityInGoal exakt wie im Draft-Beispiel
- [ ] PUT /goals mit percentSum != 100 liefert 200 (kein Fehler), rechnet DailyKcal aber nicht neu
- [ ] 400 daily-kcal-out-of-range ausserhalb 800-8000
- [ ] Rundungstabelle: Up/Down x Physiological/Declaration ueber bekannte Werte, Assertion 'nie eine Nachkommastelle in einer berechneten Ausgabe'
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0018](0018-m2-nutritiongoal-aggregate-default-profil-handler-auf-userregistered.md)
