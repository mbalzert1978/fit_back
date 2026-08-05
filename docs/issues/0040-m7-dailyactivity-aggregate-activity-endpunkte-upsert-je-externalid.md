---
id: "0040"
title: M7: DailyActivity-Aggregate + Activity-Endpunkte (Upsert je ExternalId)
status: blocked
milestone: M7
type: AFK
---

# M7: DailyActivity-Aggregate + Activity-Endpunkte (Upsert je ExternalId)

## Parent

Meilenstein [M7](docs/milestones/m7-healthsync.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

DailyActivity-Aggregate (Schluessel UserId+DiaryDate), Upsert-Invariante: ExternalId je Tag eindeutig, wiederholtes Hochladen desselben Workouts erzeugt keine Dubletten.

## Acceptance criteria

- [ ] PUT /api/v1/health/activity/{date} liefert totalKcal + entries korrekt berechnet
- [ ] Zweifaches PUT mit identischer externalId erzeugt keine zweite Zeile (Domain-Unit-Test)
- [ ] GET liefert denselben Stand
- [ ] Integrationstest, curl-Beispiel

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
