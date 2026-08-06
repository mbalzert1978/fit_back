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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/health_sync/domain/`: DailyActivity-Aggregatwurzel (Schluessel UserId+DiaryDate) mit identitaetsbasierter Gleichheit; Activity-Entitaeten mit ExternalId-Feld; Upsert-Invariante: ExternalId je Tag eindeutig (zweifaches Update mit identischer ExternalId erhaelt die existierende Zeile, ueberschreibt aber ihre Felder); Berechnung von totalKcal aus entries; **nur stdlib**
- [ ] Ein flacher, **context-eigener** `HealthSyncDomainError` (Tagged Union, ein Fall je Fehlerursache) — Fehlertyp kann geteilt mit anderen Use Cases sein
- [ ] `contexts/health_sync/application/put_activity/`: Command (date, userId, entries mit externalId/name/detail/kcal), Handler (ladet oder erzeugt DailyActivity → ruft upsert-Operation auf), Request-Mapper und Response-Mapper, Validierungsregeln, Port-Adapter
- [ ] `contexts/health_sync/application/get_activity/`: Command (date, userId), Handler, Request-Mapper und Response-Mapper, Port-Adapter
- [ ] Public Naht: zwei eigene Protokolle (GetActivityGateway, UpsertActivityGateway), **nur Primitive** ueber der Naht; jeweils eigene Tagged Union als Naht-Ergebnis
- [ ] `application/put_activity/test_api.py` + `application/put_activity/fakes/` (In-Memory)
- [ ] `application/get_activity/test_api.py` + `application/get_activity/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/health_sync/tests/put_activity/` und `contexts/health_sync/tests/get_activity/`: PUT mit zwei Entries kalkuliert totalKcal; zweifaches PUT mit identischer externalId erzeugt keine zweite Zeile, ueberschreibt aber vorhandene Felder; GET liefert denselben Stand wie PUT erzeugt hat
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen, `slice-shape-check` liefert `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert beide Naehte aus Stufe 1; Alembic-Migration fuer `health_sync.daily_activities` und `health_sync.activities`
- [ ] Upsert-Logik in der Persistierungs-Schicht: existierende Activity mit gleicher ExternalId wird identifiziert und aktualisiert (nicht eingefuegt)
- [ ] Integrationstest gegen Testcontainers-Postgres: zweifaches PUT mit identischer externalId erzeugt genau eine Zeile; GET liefert den aktuellen Stand

### Stufe 3 — HTTP

- [ ] `PUT /api/v1/health/activity/{date}` liefert 201/200 mit totalKcal + entries korrekt berechnet
- [ ] `GET /api/v1/health/activity/{date}` liefert denselben Stand
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel in der Ticket-Doku

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
