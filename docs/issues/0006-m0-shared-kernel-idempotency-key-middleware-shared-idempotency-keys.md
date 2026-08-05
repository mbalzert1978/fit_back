---
id: "0006"
title: M0: Shared Kernel - Idempotency-Key-Middleware + shared.idempotency_keys
status: blocked
milestone: M0
type: AFK
---

# M0: Shared Kernel - Idempotency-Key-Middleware + shared.idempotency_keys

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Middleware/Decorator, der den Idempotency-Key-Header (Guid) auf POST/PUT-Endpunkten auswertet: bereits verarbeiteter Key liefert die urspruengliche Antwort mit 200 statt 201, Speicherung in shared.idempotency_keys (Key, UserId, RequestHash, ResponseBody, CreatedUtc), TTL 7 Tage (Abschnitt 0.3).

## Acceptance criteria

- [ ] Zweifacher Aufruf mit demselben Idempotency-Key liefert beim zweiten Mal 200 mit identischem Body statt eines zweiten Datensatzes (Mechanismus-Test mit einem Dummy-Endpunkt)
- [ ] Eintrag landet in shared.idempotency_keys mit allen geforderten Feldern
- [ ] TTL von 7 Tagen ist als Konfigurationswert hinterlegt (Cleanup-Job selbst ist nicht Teil dieses Tickets, siehe m1-identity.md 'Nicht in Scope')

## Blocked by

- Blocked by [0003](0003-m0-alembic-grundgeruest-mit-7-schemas-identity-catalog-diary-recipes-goals-health-shared.md)
- Blocked by [0004](0004-m0-shared-kernel-result-t-e-timeprovider-protocol.md)
