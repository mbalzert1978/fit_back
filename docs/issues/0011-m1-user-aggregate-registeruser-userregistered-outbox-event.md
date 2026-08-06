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

User-Aggregate mit allen Feldern/Invarianten aus BACKEND.md Abschnitt 1 (Email eindeutig,
PasswordHash Argon2id, DisplayName, TimeZone, Locale-Union, AccountStatus-Union), Use Case
RegisterUser, Endpunkt POST /api/v1/identity/register. UserRegistered wird als Integration Event
ueber die Postgres-Outbox (M0.10) publiziert.

**Dieses Ticket ist die Referenzimplementierung der Slice-Form dieses Repos.** Es wird als erstes
echtes Feature-Slice gebaut und legt die Form fuer alle folgenden fest — `.rules/python/python-
feature-slices.md` und `.rules/python/python-rule-pattern.md` verweisen beide darauf. Nach dem
Merge zeigt `.claude/skills/review-against-rules/config.json` per `reference_implementation`
hierauf, damit kuenftige Agenten die Form nicht mehr aus Prosa rekonstruieren muessen.

**Baureihenfolge ist verbindlich und gestuft** — siehe
[`docs/milestones/00-overview.md`](../milestones/00-overview.md), „Ticket-Schnitt". Stufe 1 wird
abgenommen, **bevor** Stufe 2 beginnt. Der Slice muss ohne jede Infrastruktur vollstaendig gruen
sein.

## Acceptance criteria

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank)

- [ ] `contexts/identity/domain/`: User-Aggregatwurzel mit identitaetsbasierter Gleichheit; Value
      Objects Email/PasswordHash/DisplayName/TimeZone (`@dataclass(frozen=True, slots=True)`, per
      `parse() -> Result[...]`-Factory erzeugt, nie roher `str`); Locale/AccountStatus als
      geschlossene Tagged Unions (kein `Enum`); **nur stdlib**
- [ ] Ein flacher, **context-eigener** `DomainError` (Tagged Union, ein Fall je Fehlerursache, mit
      Nutzlast statt vorformatiertem String); Domain-Ports als `Protocol`, durchgehend
      `Result[T, E]`
- [ ] `contexts/identity/application/register_user/`: Command, Handler (orchestriert nur, ~10-15
      Zeilen, kein try/except), Request-Mapper und Response-Mapper als **getrennte** Einheiten,
      Validierungsregeln, Port-Adapter
- [ ] Public Naht des Use Case: eigenes, schmales `Protocol` mit **nur** den Operationen, die
      `register_user` braucht; **nur Primitive** ueber der Naht; eigene Tagged Union als
      Naht-Ergebnis, **nicht** `Result[T, E]`
- [ ] `application/register_user/test_api.py` + `application/register_user/fakes/` (In-Memory)
- [ ] Verhaltens-Specs unter `contexts/identity/tests/register_user/`: Arrange ueber die Test-API,
      Act ueber das echte Request-DTO, Assert gegen die echte Response-Union — abgedeckt:
      erfolgreiche Registrierung, doppelte E-Mail (case-insensitive), Passwort < 10 Zeichen
- [ ] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [ ] `./make.ps1 import-lint` gruen (Domaenen-Reinheit + Schichtung); `slice-shape-check` und
      `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur

- [ ] SQLAlchemy-Repository implementiert die Naht aus Stufe 1; Alembic-Migration fuer
      `identity.users`
- [ ] UserRegistered landet **transaktional mit dem User-Insert** in `shared.outbox`
- [ ] Integrationstest gegen Testcontainers-Postgres (eigene, aeusserste Testebene — **nicht** Teil
      der Test-API)
- [ ] Contract-Test (siehe [`02-test-pyramide.md`](../milestones/02-test-pyramide.md), Form B):
      kanonische UserRegistered-Beispiel-Payloads unter
      `contexts/identity/contracts/events/user_registered/examples/`, Roundtrip-Test belegt, dass
      jedes emittierte Event einem Beispiel entspricht

### Stufe 3 — HTTP

- [ ] `POST /api/v1/identity/register` legt einen User an und liefert 201 mit
      userId/accessToken/refreshToken/expiresInSeconds
- [ ] 409 `email-already-registered` bei doppelter E-Mail (case-insensitive)
- [ ] 400 mit `errors.password` bei Passwort < 10 Zeichen
- [ ] Idempotency-Key-Header wird ueber die M0.6-Middleware ausgewertet (zweiter Aufruf ⇒ 200)
- [ ] End-to-End-Test gegen die laufende App; curl-Beispiel in der Ticket-Doku

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
