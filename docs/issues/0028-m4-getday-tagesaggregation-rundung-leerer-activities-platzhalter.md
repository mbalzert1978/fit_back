---
id: "0028"
title: M4: GetDay (Tagesaggregation, Rundung, leerer activities-Platzhalter)
status: blocked
milestone: M4
type: AFK
---

# M4: GetDay (Tagesaggregation, Rundung, leerer activities-Platzhalter)

## Parent

Meilenstein [M4](docs/milestones/m4-diary.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

GET /api/v1/diary/days/{date} liefert date/isPlanned/goal/totals/slots(mit entries+computed)/activities. goal und computed nutzen die Rundungsregel + EnergyFactors aus M2.2. activities ist an dieser Stelle immer ein leeres Array (HealthSync existiert erst ab M7).

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/diary/application/get_day/`: Command (userId, date), Handler (ladet DiaryDay + User-Profil fuer Rundungseinstellung → aggregiert Entries pro Slot → rechnet Goal + Computed per Slot + Gesamt → appliziert Rundung → prueft isPlanned-Bedingung → gibt Outcome zurueck), Request-Mapper und Response-Mapper als **getrennte** Einheiten
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` fuer DiaryDay-Ladevorgang und User-Profil-Abruf; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/get_day/test_api.py` + `application/get_day/fakes/` (In-Memory, fake DiaryDay- und User-Gateway mit konfigurierbarer Rundungseinstellung)
- [ ] Verhaltens-Specs unter `contexts/diary/specs/get_day/`: Aggregation von Entries pro Slot, computed nach Nutzer-Rundungseinstellung gerundet, nutrientsPer100 ungerundet, isPlanned=true bei date > heute, isPlanned=false bei date <= heute, activities = leeres Array
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container** — verwendet gefakete Zeitzone + TimeProvider (M0.4)

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1: ladet DiaryDay + abhaengige Entries, berechnet Aggregationen
- [ ] Port-Adapter fuer User-Profil-Abruf (Rundungseinstellung, Zeitzone)
- [ ] Integrationstest gegen Testcontainers-Postgres: Aggregation, Rundung, isPlanned-Bedingung

### Stufe 3 — HTTP

- [ ] `GET /api/v1/diary/days/{date}` liefert vollstaendige Tagesaggregation
- [ ] Response-Schema exakt wie im Draft-Beispiel (Abschnitt 3): date, isPlanned, goal, totals (Grundsummen), slots (array mit entries + computed pro Slot), activities (leeres Array)
- [ ] computed-Bloecke sind nach der Nutzer-Rundungseinstellung gerundet, nutrientsPer100 bleibt ungerundet
- [ ] isPlanned=true wenn date > heute in der Zeitzone des Nutzers
- [ ] activities ist ein leeres Array (Platzhalter fuer M7.4)
- [ ] 404 wenn DiaryDay nicht existiert (leer sein ist ok, aber Slot-Struktur muss existieren von 0026 her)
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel

## Blocked by

- Blocked by [0027](0027-m4-diaryday-diaryentry-aggregate-addentry-kopiersemantik-zusammenfassen.md)
- Blocked by [0019](0019-m2-getgoals-updategoals-gramm-prozent-ableitung-rundung.md)
