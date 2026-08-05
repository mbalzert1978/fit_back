---
id: "0011"
title: M1: User-Aggregate + RegisterUser + UserRegistered-Outbox-Event
status: blocked
milestone: M1
type: AFK
---

# M1: User-Aggregate + RegisterUser + UserRegistered-Outbox-Event

## Parent

Meilenstein [M1](docs/milestones/m1-identity.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

User-Aggregate mit allen Feldern/Invarianten aus BACKEND.md Abschnitt 1 (Email eindeutig, PasswordHash Argon2id, DisplayName, TimeZone, Locale-Union, AccountStatus-Union), Use Case RegisterUser, Endpunkt POST /api/v1/identity/register. Empfehlung: dieses Feature als Referenz-Feature etablieren (siehe .rules/python/python-rule-pattern.md und python-feature-slices.md, die beide darauf verweisen) und anschliessend review-against-rules/config.json's reference_implementation darauf aktualisieren. UserRegistered wird als Integration Event ueber die Postgres-Outbox (M0.10) publiziert.

## Acceptance criteria

- [ ] POST /api/v1/identity/register legt einen User an und liefert 201 mit userId/accessToken/refreshToken/expiresInSeconds
- [ ] 409 email-already-registered bei doppelter E-Mail (case-insensitive)
- [ ] 400 mit errors.password bei Passwort < 10 Zeichen
- [ ] UserRegistered landet transaktional mit dem User-Insert in shared.outbox
- [ ] Idempotency-Key-Header wird ueber die M0.6-Middleware ausgewertet (zweiter Aufruf ⇒ 200)
- [ ] Domain-Unit-Tests fuer alle Invarianten, Value-Object-Tests fuer Email/PasswordHash/DisplayName/TimeZone, Architekturtest (kein rohes Primitive, kein enum), Tagged-Union-Serialisierungstest fuer Locale/AccountStatus
- [ ] Integrationstest gegen Testcontainers-Postgres, curl-Beispiel in der Ticket-Doku
- [ ] Contract-Test (siehe docs/milestones/02-test-pyramide.md, Form B): kanonische UserRegistered-Beispiel-Payloads liegen unter contexts/identity/contracts/events/user_registered/examples/, ein Roundtrip-Test belegt, dass jedes tatsaechlich emittierte Event einem dieser Beispiele entspricht

## Blocked by

- Blocked by [0001](0001-m0-repo-skeleton-docker-compose-postgres-minio-app-health-endpoint-curl-smoke-test.md)
- Blocked by [0002](0002-m0-ruff-konfiguration-import-linter-contract-lint-ci-schritt.md)
- Blocked by [0003](0003-m0-alembic-grundgeruest-mit-7-schemas-identity-catalog-diary-recipes-goals-health-shared.md)
- Blocked by [0004](0004-m0-shared-kernel-result-t-e-timeprovider-protocol.md)
- Blocked by [0005](0005-m0-shared-kernel-rfc-7807-problemdetails-exception-handler.md)
- Blocked by [0006](0006-m0-shared-kernel-idempotency-key-middleware-shared-idempotency-keys.md)
- Blocked by [0007](0007-m0-shared-kernel-iuserowned-mixin-uuidv7-helper-rowversion-if-match.md)
- Blocked by [0009](0009-m0-pytest-testcontainers-postgres-fixture.md)
- Blocked by [0010](0010-m0-shared-kernel-postgres-outbox-event-relay-skip-locked-listen-notify.md)
