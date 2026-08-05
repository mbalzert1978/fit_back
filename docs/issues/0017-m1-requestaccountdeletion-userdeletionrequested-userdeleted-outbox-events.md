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

- [ ] DELETE /api/v1/identity/me liefert 202 mit deletionEffectiveUtc
- [ ] Status des Nutzers ist danach PendingDeletion(EffectiveAt)
- [ ] Ein PendingDeletion-Konto kann sich nachweislich nicht mehr anmelden (Domain-Unit-Test, Integrationstest zusammen mit M1.2)
- [ ] UserDeletionRequested landet transaktional in shared.outbox
- [ ] curl-Beispiel
- [ ] Contract-Test (siehe docs/milestones/02-test-pyramide.md, Form B): kanonische Beispiel-Payloads fuer UserDeletionRequested UND UserDeleted liegen unter contexts/identity/contracts/events/<event>/examples/, ein Roundtrip-Test belegt, dass jedes tatsaechlich emittierte Event einem dieser Beispiele entspricht

## Blocked by

- Blocked by [0011](0011-m1-user-aggregate-registeruser-userregistered-outbox-event.md)
