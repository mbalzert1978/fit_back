---
id: "0030"
title: M4: GetRecent
status: blocked
milestone: M4
type: AFK
---

# M4: GetRecent

## Parent

Meilenstein [M4](docs/milestones/m4-diary.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

GET /api/v1/diary/recent?take= liefert die zuletzt erfassten Produkte UND Rezepte gemischt, absteigend nach letzter Verwendung (Rezepte bleiben bis M6 leer/ungenutzt in dieser Liste).

## Acceptance criteria

- [ ] Response liefert sourceType/sourceId/displayName/lastGrams/lastUsedUtc/kcalPerPortion, korrekt absteigend sortiert
- [ ] take-Parameter begrenzt die Ergebnisliste
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0027](0027-m4-diaryday-diaryentry-aggregate-addentry-kopiersemantik-zusammenfassen.md)
