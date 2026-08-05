---
id: "0041"
title: M7: nutrition-export-Endpunkt
status: blocked
milestone: M7
type: AFK
---

# M7: nutrition-export-Endpunkt

## Parent

Meilenstein [M7](docs/milestones/m7-healthsync.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

GET /api/v1/health/nutrition-export/{date} - liefert die Tageswerte (kcal/carbsG/proteinG/fatG) fuer den Client, der sie selbst in HealthKit schreibt.

## Acceptance criteria

- [ ] Response liefert dieselben aggregierten Werte wie Diary.GetDay.totals fuer denselben Tag
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0028](0028-m4-getday-tagesaggregation-rundung-leerer-activities-platzhalter.md)
