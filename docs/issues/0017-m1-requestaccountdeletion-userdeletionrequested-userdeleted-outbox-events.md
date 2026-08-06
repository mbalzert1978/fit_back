---
id: "0017"
title: M1: RequestAccountDeletion + UserDeletionRequested/UserDeleted-Outbox-Events
status: blocked
milestone: M1
type: AFK
---

# M1: RequestAccountDeletion + UserDeletionRequested/UserDeleted-Outbox-Events

## Parent

Meilenstein [M1](docs/milestones/m1-identity.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Use Case RequestAccountDeletion() setzt Status PendingDeletion (Loeschung nach 30 Tagen per Hintergrundjob - der Job selbst ist eigenes, spaeter vergebbares Ticket), publiziert UserDeletionRequested ueber die Outbox (M0.10). UserDeleted wird analog vorbereitet, damit jeder spaetere Context (M2, M3, M4, M6, M7) unabhaengig einen eigenen Konsumenten ergaenzen kann.

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/identity/domain/`: RequestAccountDeletionError als Tagged Union (AccountAlreadyPendingDeletion); Invariante im User-Aggregat: Status wechselt von Active/AccountStatus zu PendingDeletion(EffectiveAt); Ein PendingDeletion-Konto kann sich nicht mehr anmelden
- [ ] `contexts/identity/application/request_account_deletion/`: Command (userId), Handler (orchestriert nur, setzt Status, generiert EffectiveAt), Request-Mapper und Response-Mapper als **getrennte** Einheiten
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` fuer Status-Update; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/request_account_deletion/test_api.py` + `application/request_account_deletion/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/identity/specs/request_account_deletion/`: erfolgreiches Setzen auf PendingDeletion, bereits-pending-Konto lehnt Anfrage ab, angemeldeter Status ist danach nachweislich PendingDeletion(EffectiveAt)
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1, aktualisiert User-Status
- [ ] UserDeletionRequested und UserDeleted landen **transaktional mit dem Status-Update** in `shared.outbox` (M0.10)
- [ ] Contract-Test (siehe `docs/milestones/02-test-pyramide.md`, Form B): kanonische Beispiel-Payloads fuer UserDeletionRequested UND UserDeleted liegen unter `contexts/identity/contracts/events/<event>/examples/`, ein Roundtrip-Test belegt, dass jedes emittierte Event einem dieser Beispiele entspricht
- [ ] Integrationstest gegen Testcontainers-Postgres: Status-Update ist transaktional mit Outbox-Publikation, kein Event ohne Status-Aenderung

### Stufe 3 — HTTP

- [ ] `DELETE /api/v1/identity/me` setzt den Status auf PendingDeletion und liefert 202 mit deletionEffectiveUtc
- [ ] Ein PendingDeletion-Konto kann sich nachweislich nicht mehr anmelden (koordiniert mit 0012-Login-Test)
- [ ] End-to-End-Test; curl-Beispiel

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
