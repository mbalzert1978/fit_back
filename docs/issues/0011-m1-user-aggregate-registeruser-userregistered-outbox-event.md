---
id: "0011"
title: M1: User-Aggregate + RegisterUser + UserRegistered-Outbox-Event
status: open
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

### Stufe 1 — Slice (ohne Infrastruktur, ohne HTTP, ohne Datenbank) — **abgeschlossen (2026-08-06)**

Gebaut auf Branch `0011-register-user-slice`. Der Slice ist damit die
Referenzimplementierung: `.claude/skills/review-against-rules/config.json` zeigt per
`reference_implementation` darauf, ebenso die Kopfnotizen von
`.rules/python/python-feature-slices.md` und `.rules/python/python-rule-pattern.md`.

Zwei Ergaenzungen ausserhalb des Slice, beide in
[`2026-08-06-…-shared-kernel-validation-und-tzdata.md`](../decisions/2026-08-06-1105-shared-kernel-validation-und-tzdata.md)
begruendet: `src/shared_kernel/validation.py` (Collect-all Rule Pattern) und `tzdata` als
Laufzeit-Dependency.

- [x] `contexts/identity/domain/`: User-Aggregatwurzel mit identitaetsbasierter Gleichheit; Value
      Objects Email/PasswordHash/DisplayName/TimeZone (`@dataclass(frozen=True, slots=True)`, per
      `parse() -> Result[...]`-Factory erzeugt, nie roher `str`); Locale/AccountStatus als
      geschlossene Tagged Unions (kein `Enum`); **nur stdlib**
- [x] Ein flacher, **context-eigener** `DomainError` (Tagged Union, ein Fall je Fehlerursache, mit
      Nutzlast statt vorformatiertem String); Domain-Ports als `Protocol`, durchgehend
      `Result[T, E]`
- [x] `contexts/identity/application/register_user/`: Command, Handler (orchestriert nur, ~10-15
      Zeilen, kein try/except), Request-Mapper und Response-Mapper als **getrennte** Einheiten,
      Validierungsregeln, Port-Adapter
- [x] Public Naht des Use Case: eigenes, schmales `Protocol` mit **nur** den Operationen, die
      `register_user` braucht; **nur Primitive** ueber der Naht; eigene Tagged Union als
      Naht-Ergebnis, **nicht** `Result[T, E]`
- [x] `application/register_user/test_api.py` + `application/register_user/fakes/` (In-Memory)
- [x] Verhaltens-Specs unter `contexts/identity/specs/register_user/`: Arrange ueber die Test-API,
      Act ueber das echte Request-DTO, Assert gegen die echte Response-Union — abgedeckt:
      erfolgreiche Registrierung, doppelte E-Mail (case-insensitive), Passwort < 10 Zeichen
- [x] **Diese Specs sind gruen ohne Datenbank, ohne HTTP, ohne Container**
- [x] `./make.ps1 import-lint` gruen (Domaenen-Reinheit + Schichtung); `slice-shape-check` und
      `structure-placement-check` liefern `Findings: 0`

### Stufe 2 — Infrastruktur — **bis auf den Contract-Test abgeschlossen (2026-08-06, PR #11)**

- [x] SQLAlchemy-Repository implementiert die Naht aus Stufe 1
      (`contexts/identity/infrastructure/persistence/user_store.py`); Alembic-Migration fuer
      `identity.users` (`alembic/identity/versions/002_create_users_table.py`)
- [x] UserRegistered landet **transaktional mit dem User-Insert** in `shared_kernel.outbox`
      (belegt durch `tests/contexts/identity/test_register_user_persistence.py`,
      `test_nutzer_und_ereignis_entstehen_gemeinsam` / `test_ohne_commit_entsteht_keine_von_beiden`)
- [x] Integrationstest gegen Testcontainers-Postgres (eigene, aeusserste Testebene — **nicht** Teil
      der Test-API): `tests/contexts/identity/test_register_user_persistence.py`, 6 Faelle
- [ ] **Offen —** Contract-Test (siehe
      [`02-test-pyramide.md`](../milestones/02-test-pyramide.md), Form B). Heute existiert nur
      `contexts/identity/contracts/user_registered.py`; das Verzeichnis `events/…/examples/` gibt es
      nicht. Zu bauen:
  - Kanonische Beispiel-Payloads als **je eine `.json`-Datei** unter
    `contexts/identity/contracts/events/user_registered/examples/`, Dateiname
    `<version>-<fall>.json` (z. B. `v1-vollstaendig.json`).
  - Jede Payload traegt **alle** Felder, die die Konsumenten aus `docs/Draft/BACKEND.md:109`
    brauchen (Goals fuer das Default-Profil, Diary fuer die Standard-Mahlzeiten-Slots) — mindestens
    `userId`, `email`, `locale`, `timeZoneId`, `registeredAt`. Ein Feld, das kein Konsument liest,
    gehoert nicht in die Payload.
  - Roundtrip-Test belegt, dass jedes emittierte Event **genau** einem Beispiel entspricht
    (Feldmenge identisch, nicht nur Teilmenge).
  - **Bei Abweichung ist die Beispiel-Datei massgeblich**, nicht der Produktionscode: sie ist der
    veroeffentlichte Vertrag. Ein Feld darf additiv dazukommen (neue Beispiel-Datei mit erhoehter
    `<version>`); Umbenennen oder Entfernen eines Feldes ist ein Bruch und braucht ein eigenes
    Ticket, das die Konsumenten mitzieht.

### Stufe 3 — HTTP — **abgeschlossen (2026-08-06, PR #11)**

- [x] `POST /api/v1/identity/register` legt einen User an und liefert 201 mit
      `userId`/`email`/`displayName`/`locale`/`timeZoneId`/`registeredAt`
      (`src/api/identity/register_user_router.py`)
- [x] 409 `email-already-registered` bei doppelter E-Mail (case-insensitive)
- [x] 400 mit `errors.password` bei Passwort < 10 Zeichen
- [x] End-to-End-Test gegen die aus Router und Exception-Handlern gebaute App vor
      Testcontainers-Postgres: `tests/api/test_register_user_endpoint.py`, 5 Faelle. `main.py` wird
      bewusst **nicht** importiert (Begruendung im Modul-Docstring dort).
- [x] curl-Beispiel — siehe „Aufruf-Beispiel" unten in diesem Ticket

**Nach 0012 verschoben** (siehe
[`2026-08-07-0633-register-liefert-noch-keine-tokens.md`](../decisions/2026-08-07-0633-register-liefert-noch-keine-tokens.md)):
`accessToken`/`refreshToken`/`expiresInSeconds` in der 201-Antwort und der Idempotenz-Nachweis
(zweiter Aufruf ⇒ 200). Beides haengt an der Auth-Middleware aus 0012 — die Idempotency-Middleware
aus 0006 steigt ohne `request.state.user_id` bewusst aus
(`src/middleware/idempotency.py:257-259`). Der Endpunkt haengt bereits hinter der Middleware; dass
sie fuer ihn wirkungslos bleibt, ist ein **dokumentiertes Provisorium**, kein Defekt.

## Bewusst nicht in diesem Ticket

- **`RowVersion`/Optimistic Concurrency** (`docs/Draft/BACKEND.md:80`, Ticket 0007). `identity.users`
  hat heute keine `row_version`-Spalte, und im ganzen Repo existiert der Begriff nicht. Fuer
  `RegisterUser` braucht es sie auch nicht: das Aggregate entsteht hier, es wird nichts nebenlaeufig
  ueberschrieben, und es gibt kein `If-Match` auf einem `POST`. Die Spalte kommt mit dem ersten
  Use Case, der einen **bestehenden** User aendert (UpdateProfile / ChangePassword) — dort wird sie
  zum Kriterium.
- **Defaults fuer `timeZoneId` und `locale`.** `docs/Draft/BACKEND.md:98-99` nennt Defaults, im
  Request-Body sind beide **Pflichtfelder**. Verbindlich fuer dieses Ticket: der Default gilt
  **nicht** auf API-Ebene — wer registriert, schickt beide Werte, ein fehlendes Feld ist 400. Ein
  Default in der Domaene waere ein zweiter Ort fuer dieselbe Regel und entfaellt damit ebenfalls.
  Bequemlichkeits-Defaults gehoeren, wenn ueberhaupt, in den Client.

## Aufruf-Beispiel

```bash
curl -i -X POST http://localhost:8000/api/v1/identity/register \
  -H 'Content-Type: application/json' \
  -d '{
        "email": "markus@example.de",
        "password": "ein-langes-passwort",
        "displayName": "Markus",
        "locale": "de",
        "timeZoneId": "Europe/Berlin"
      }'
```

Antwort `201 Created`:

```json
{
  "userId": "0198e0c1-...",
  "email": "markus@example.de",
  "displayName": "Markus",
  "locale": "de",
  "timeZoneId": "Europe/Berlin",
  "registeredAt": "2026-08-06T12:05:00+00:00"
}
```

Zweiter Aufruf mit derselben Adresse: `409` mit
`{"type": ".../email-already-registered", ...}`. Passwort unter 10 Zeichen: `400` mit
gefuelltem `errors.password`.

## Was der Slice am bisherigen Stand geaendert hat

Fuer Nachfolge-Tickets, die auf denselben Bausteinen aufsetzen:

- `not_blank` ist zu `NotEmptyString` geworden — die Invariante „getrimmt und nicht leer" liegt
  einmal im Shared Kernel (`src/contexts/shared_kernel/not_empty_string.py`), nicht in jedem Value
  Object.
- `Result` hat `map_err` und `inspect_async` bekommen (`src/contexts/shared_kernel/result.py`).
- `claim_email` und `find_by_email` sind **ersatzlos entfallen**: ueber die Eindeutigkeit
  entscheidet der Unique-Constraint per `INSERT ... ON CONFLICT DO NOTHING RETURNING id`, nicht ein
  vorgelagertes SELECT (Begruendung im Kopf von `user_store.py`).
- `src/contexts/shared_kernel/validation.py` (Collect-all Rule Pattern) und `tzdata` als
  Laufzeit-Dependency sind neu, begruendet in
  [`2026-08-06-1105-shared-kernel-validation-und-tzdata.md`](../decisions/2026-08-06-1105-shared-kernel-validation-und-tzdata.md).

## Blocked by

- Blocked by [0001](0001-m0-repo-skeleton-docker-compose-postgres-minio-app-health-endpoint-curl-smoke-test.md)
- Blocked by [0002](0002-m0-ruff-konfiguration-import-linter-contract-lint-ci-schritt.md)
- Blocked by [0003](0003-m0-alembic-grundgeruest-mit-7-schemas-identity-catalog-diary-recipes-goals-health-shared.md)
- Blocked by [0004](0004-m0-shared-kernel-result-t-e-timeprovider-protocol.md)
- Blocked by [0005](0005-m0-shared-kernel-rfc-7807-problemdetails-exception-handler.md)
- Blocked by [0006](0006-m0-shared-kernel-idempotency-key-middleware-shared-idempotency-keys.md)
- Blocked by [0007](0007-m0-shared-kernel-iuserowned-mixin-uuidv7-helper-rowversion-if-match.md) — **nur der UUIDv7-Helper**; `RowVersion`/`If-Match` sind hier ausdruecklich nicht im Schnitt (siehe „Bewusst nicht in diesem Ticket")
- Blocked by [0009](0009-m0-pytest-testcontainers-postgres-fixture.md) — **nur Stufe 2 und 3**
- Blocked by [0010](0010-m0-shared-kernel-postgres-outbox-event-relay-skip-locked-listen-notify.md) — **nur Stufe 2**; Stufe 1 ist davon unabhaengig

**Nicht** blockiert durch 0012: die frueher hier gefuehrte Token-Rueckgabe ist nach 0012 verschoben
(Entscheidung vom 2026-08-07). Damit ist der Zyklus 0011 ↔ 0012 aufgeloest.

## Restarbeit bis zum Abschluss

Einziger offener Punkt ist der **Contract-Test** in Stufe 2. Alles andere ist gebaut, gemergt und
oben abgehakt — wer dieses Ticket aufnimmt, baut nichts davon neu.
