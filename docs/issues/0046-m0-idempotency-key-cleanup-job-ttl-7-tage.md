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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `shared_kernel/domain/`: CleanupExpiredIdempotencyKeysError als Tagged Union (falls noetig); Invarianten: nur Eintraege aelter als 7 Tage werden geloescht, juengere bleiben erhalten
- [ ] `shared_kernel/application/cleanup_idempotency_keys/`: Command (current time), Handler (ladet abgelaufene Idempotency-Key-Eintraege, loescht sie), Request-Mapper und Response-Mapper, Validierungsregeln, Port-Adapter
- [ ] Public Naht: eigenes, schmales `Protocol` zum Laden und Loeschen abgelaufener Eintraege; **nur Primitive** ueber der Naht; eigene Tagged Union als Naht-Ergebnis
- [ ] `application/cleanup_idempotency_keys/test_api.py` + `application/cleanup_idempotency_keys/fakes/` (In-Memory, Fake-TimeProvider)
- [ ] Verhaltens-Specs unter `shared_kernel/tests/cleanup_idempotency_keys/`: Ein Eintrag aelter als 7 Tage wird zuverlaessig als zu loeschen identifiziert; ein Eintrag juenger bleibt erhalten; Loeschlogik ist unabhaengig von aktueller Zeit (verwaltet mit gefaketer TimeProvider)
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container** — Gateway ist gefakt, Zeit wird gefakt
- [ ] `./make.ps1 import-lint` gruen, `slice-shape-check` liefert `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1; Abfrage auf `CreatedUtc` < (now - 7 days)
- [ ] Job-Scheduler/Hintergrundjob (analog zu OCR-Job-Mechanismus aus M5): Periodisch (z.B. stundlich) werden Eintraege mit `CreatedUtc` aelter als 7 Tage geloescht
- [ ] Integrationstest gegen Testcontainers-Postgres mit gefaketer Zeit (TimeProvider): Eintrag aelter als 7 Tage wird geloescht, juengerer bleibt erhalten; Job laeuft periodisch ohne manuellen Eingriff

## Stufe 3 — HTTP

Kein HTTP-Endpunkt erforderlich — dies ist ein Hintergrundjob

## Blocked by

- Blocked by [0006](0006-m0-shared-kernel-idempotency-key-middleware-shared-idempotency-keys.md)
