---
id: "0004"
title: M0: Shared Kernel - Result[T,E] + TimeProvider-Protocol
status: blocked
milestone: M0
type: AFK
---

# M0: Shared Kernel - Result[T,E] + TimeProvider-Protocol

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Result[T,E]-Basistyp gemaess .rules/python/python-error-handling.md sowie ein TimeProvider-Protocol (Abschnitt 0.12: nie datetime.utcnow() direkt) mit einer Standard- und einer Fake-Implementierung fuer Tests, im shared_kernel-Paket.

## Acceptance criteria

- [ ] Result[T,E] unterstuetzt .bind()/.map() und ist per Unit-Test abgedeckt
- [ ] TimeProvider.utc_now() liefert DateTimeOffset (bzw. das Python-Aequivalent mit tz-aware datetime), FakeTimeProvider erlaubt deterministisches Setzen der Zeit in Tests
- [ ] Architekturtest: kein Modul unter src/ ruft datetime.utcnow()/datetime.now() ohne tz direkt auf

## Blocked by

- Blocked by [0001](0001-m0-repo-skeleton-docker-compose-postgres-minio-app-health-endpoint-curl-smoke-test.md)
