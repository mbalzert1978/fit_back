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

- [ ] Response-Schema exakt wie im Draft-Beispiel (Abschnitt 3)
- [ ] computed-Bloecke sind nach der Nutzer-Rundungseinstellung gerundet, nutrientsPer100 bleibt ungerundet
- [ ] isPlanned=true wenn date > heute in der Zeitzone des Nutzers
- [ ] activities ist ein leeres Array (Platzhalter fuer M7.4)
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0027](0027-m4-diaryday-diaryentry-aggregate-addentry-kopiersemantik-zusammenfassen.md)
- Blocked by [0019](0019-m2-getgoals-updategoals-gramm-prozent-ableitung-rundung.md)
