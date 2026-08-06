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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/diary/application/get_recent_sources/`: Command (userId, take), Handler (ladet zuletzt verwendete DiaryEntrys pro Nutzer → extrahiert distinct Products/Recipes sortiert nach lastUsedUtc absteigend → begrenzt auf take-Wert → mappt zu Response), Request-Mapper und Response-Mapper
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` fuer Abruf der zuletzt verwendeten Sources; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/get_recent_sources/test_api.py` + `application/get_recent_sources/fakes/` (In-Memory, fake DiaryEntry/Source-Gateway)
- [ ] Verhaltens-Specs unter `contexts/diary/tests/get_recent_sources/`: Quellen korrekt sortiert (absteigend nach lastUsedUtc), take-Parameter limitiert Ergebnisliste, sourceType und sourceId korrekt gemappt, lastGrams und kcalPerPortion aus letztem Entry, leere Liste wenn nichts erfasst
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1: Query nach DiaryEntrys absteigend nach created/updated, Deduplizierung nach SourceId/SourceType, Mapping zu sourceType/sourceId/displayName/lastGrams/lastUsedUtc/kcalPerPortion
- [ ] Integrationstest gegen Testcontainers-Postgres: Mehrere Entries verschiedener Sources, korrekte Sortierung, take-Limitierung

### Stufe 3 — HTTP

- [ ] `GET /api/v1/diary/recent?take=10` liefert zuletzt erfasste Produkte UND Rezepte gemischt
- [ ] Response-Array mit sourceType (Product/Recipe), sourceId, displayName, lastGrams, lastUsedUtc (ISO 8601), kcalPerPortion
- [ ] take-Parameter (optional, default z.B. 10) begrenzt die Ergebnisliste
- [ ] Sortierung absteigend nach lastUsedUtc
- [ ] Rezepte bleiben bis M6 leer/ungenutzt in dieser Liste
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel

## Blocked by

- Blocked by [0027](0027-m4-diaryday-diaryentry-aggregate-addentry-kopiersemantik-zusammenfassen.md)
