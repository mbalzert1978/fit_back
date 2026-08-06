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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/diary/domain/ports/`: Neuer `HealthActivityGateway` Protocol (Anti-Corruption-Layer), definiert die schmale Schnittstelle fuer das Laden der Aktivitaeten aus HealthSync; **nur Primitive** ueber der Naht
- [ ] `contexts/diary/application/get_day/`: GetDay-Handler erweitert, ruft ueber den neuen Gateway die Aktivitaeten auf (oder ein leeres Array, wenn nicht verbunden), integriert sie in den Day-Aggregat
- [ ] Verhaltens-Specs unter `contexts/diary/tests/get_day/`: GetDay liefert bei verfuegbarem Gateway echte activities-Eintraege (name/detail/kcal); ohne Gateway ein leeres Array; **Diese Specs laufen mit In-Memory-Fake des Gateways, ohne Datenbank, ohne Container**
- [ ] `./make.ps1 import-lint` gruen: kein direkter Import von HealthSync-Domain/Handler-Code aus Diary

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-basierter In-Process-Adapter implementiert `HealthActivityGateway` aus Stufe 1: ruft HealthSync's Application-Service auf (kein HTTP, kein RPC), uebersetzt Ergebnis in Primitive
- [ ] **Contract-Test** (siehe docs/milestones/02-test-pyramide.md, Form A): Diary definiert eine implementierungsunabhaengige Test-Suite `assert_health_activity_gateway_contract(gateway)` unter `contexts/diary/tests/contracts/`, HealthSync importiert sie und fuehrt sie gegen seinen eigenen In-Process-Adapter aus
- [ ] Integrationstest End-to-End gegen Testcontainers-Postgres ueber M4.4 + M7.2 + M7.4: GetDay liefert die echten DailyActivity-Daten aus HealthSync

## Stufe 3 — HTTP

GetDay wird bereits in M4.4 publiziert und aendert kein HTTP-Verhalten; diese Erweiterung hat keine neue Stufe 3

## Blocked by

- Blocked by [0040](0040-m7-dailyactivity-aggregate-activity-endpunkte-upsert-je-externalid.md)
- Blocked by [0028](0028-m4-getday-tagesaggregation-rundung-leerer-activities-platzhalter.md)
