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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/health_sync/application/export_nutrition/`: Command (date, userId), Handler (ruft Diary ueber den Port auf und transformiert Ergebnis zu Response), Request-Mapper und Response-Mapper
- [ ] Public Naht: eigenes, schmales `Protocol` mit Operation zum Laden der Tageswerte aus Diary; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/export_nutrition/test_api.py` + `application/export_nutrition/fakes/` (In-Memory, Fake-Gateway zu Diary)
- [ ] Verhaltens-Specs unter `contexts/health_sync/tests/export_nutrition/`: Projektion der Diary-Daten (kcal/carbsG/proteinG/fatG) in Export-Format, Verhalten des Gateway-Adapters
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container** — Gateway ist gefakt
- [ ] `./make.ps1 import-lint` gruen, `slice-shape-check` liefert `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] Port-Adapter implementiert die Naht aus Stufe 1: ruft Diary's Application-Service fuer GetDay auf (In-Process, kein HTTP), uebersetzt Ergebnis
- [ ] Integrationstest gegen Testcontainers-Postgres + echte Diary/HealthSync-Daten: Response liefert dieselben aggregierten Werte wie Diary.GetDay.totals fuer denselben Tag

### Stufe 3 — HTTP

- [ ] `GET /api/v1/health/nutrition-export/{date}` liefert 200 mit kcal/carbsG/proteinG/fatG
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel in der Ticket-Doku

## Blocked by

- Blocked by [0028](0028-m4-getday-tagesaggregation-rundung-leerer-activities-platzhalter.md)
