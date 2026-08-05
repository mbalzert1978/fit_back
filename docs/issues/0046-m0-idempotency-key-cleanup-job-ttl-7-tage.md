---
id: "0046"
title: "M0: Idempotency-Key-Cleanup-Job (TTL 7 Tage)"
status: blocked
milestone: M0
type: AFK
---

# M0: Idempotency-Key-Cleanup-Job (TTL 7 Tage)

## Parent

Meilenstein [M0](../milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen
fachlichen Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Hintergrundjob (analog zum OCR-Job-Mechanismus aus M5, Postgres-nativ, kein separater Scheduler
noetig), der Eintraege in `shared.idempotency_keys` entfernt, deren `CreatedUtc` aelter als 7 Tage
ist (Abschnitt 0.3). Laeuft periodisch im selben Deployment.

## Acceptance criteria

- [ ] Ein Eintrag aelter als 7 Tage wird vom Job zuverlaessig entfernt
- [ ] Ein Eintrag juenger als 7 Tage bleibt erhalten
- [ ] Der Job laeuft periodisch ohne manuellen Eingriff (Integrationstest mit gefaketer Zeit ueber
      TimeProvider aus M0.4)

## Blocked by

- Blocked by [0006](0006-m0-shared-kernel-idempotency-key-middleware-shared-idempotency-keys.md)
