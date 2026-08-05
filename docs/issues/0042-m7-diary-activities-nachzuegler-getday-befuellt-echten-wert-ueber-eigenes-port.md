---
id: "0042"
title: M7: Diary-activities-Nachzuegler (GetDay befuellt echten Wert ueber eigenes Port)
status: blocked
milestone: M7
type: AFK
---

# M7: Diary-activities-Nachzuegler (GetDay befuellt echten Wert ueber eigenes Port)

## Parent

Meilenstein [M7](docs/milestones/m7-healthsync.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Diary definiert ein eigenes schmales HealthActivityGateway-Protocol (Anti-Corruption-Layer, siehe 'Cross-Context-Kommunikation') und ruft darueber synchron HealthSync's Application-Service auf, um den bisher leeren activities-Block aus M4.4 mit echten DailyActivity-Daten zu befuellen.

## Acceptance criteria

- [ ] GetDay liefert bei verbundenem HealthSync die echten activities-Eintraege (name/detail/kcal), bei nicht verbundenem weiterhin ein leeres Array
- [ ] Kein direkter Import von HealthSync-Domain/Handler-Code aus Diary
- [ ] Integrationstest End-to-End ueber M4.4 + M7.2 + M7.4, curl-Beispiel
- [ ] Contract-Test (siehe docs/milestones/02-test-pyramide.md, Form A): Diary definiert eine implementierungsunabhaengige Test-Suite assert_health_activity_gateway_contract(gateway) unter contexts/diary/tests/contracts/, HealthSync importiert sie und fuehrt sie gegen seinen eigenen In-Process-Adapter aus

## Blocked by

- Blocked by [0040](0040-m7-dailyactivity-aggregate-activity-endpunkte-upsert-je-externalid.md)
- Blocked by [0028](0028-m4-getday-tagesaggregation-rundung-leerer-activities-platzhalter.md)
