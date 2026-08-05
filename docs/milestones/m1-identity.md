# M1 — Identity & Access + Fehlerformat + Auth-Pipeline

**Bezug BACKEND.md:** Abschnitt 1, Abschnitt 8.1.
**Voraussetzung:** M0.

## Ziel

Registrierung, Login, Refresh/Logout, Profilverwaltung, Konto-Löschung. Erste vollständige
vertikale Slices (Domain → Application → API → Tests) — etabliert das Referenz-Feature, auf das
`.rules/python/python-rule-pattern.md` und `.rules/python/python-feature-slices.md` bereits
verweisen ("Sobald dieses Projekt ein erstes Referenz-Feature hat, diese Datei darauf verweisen
lassen"). **Empfehlung:** `register_user` als Referenz-Feature wählen und
`review-against-rules/config.json`s `reference_implementation` danach aktualisieren (siehe
`01-technical-decisions.md`).

## Scope

Aggregates: `User`, `RefreshToken` (Abschnitt 1).

Use Cases: `RegisterUser`, `Login`, `RefreshSession`, `Logout`, `UpdateProfile`,
`ChangePassword`, `RequestAccountDeletion`.

API: `POST /api/v1/identity/register`, `POST /api/v1/identity/login`,
`POST /api/v1/identity/refresh`, `POST /api/v1/identity/logout`, `GET /api/v1/identity/me`,
`PATCH /api/v1/identity/me`, `POST /api/v1/identity/me/password`, `DELETE /api/v1/identity/me`.

Zusätzlich (technisch, aber hier verortet, weil ohne sie kein anderer Context lauffähig ist):

- JWT-Auth-Pipeline (Access 15 min, Refresh 60 Tage rotierend, Wiederverwendung eines revoked
  Tokens ⇒ alle Tokens des Nutzers revoken).
- RFC-7807-Fehlerantworten für alle Identity-Fehlerfälle (`email-already-registered`,
  `invalid-credentials`, `account-pending-deletion`, Validierungsfehler).
- `UserRegistered`-Domain-Event (In-Process, MediatR-Äquivalent) — Konsumenten sind M2 (Goals:
  Default-Zielprofil) und M4 (Diary: drei Standard-Slots) und dürfen zu diesem Zeitpunkt noch
  nicht existieren; das Event selbst und sein Publizieren gehören zu M1, die beiden Handler ziehen
  in M2/M4 nach.
- `UserDeletionRequested`/`UserDeleted`-Events (Publizieren hier; Konsumenten in jedem späteren
  Context, sobald der jeweilige Context existiert — je ein kleines Nachfolge-Ticket pro Context ab
  M2).

## Nicht in Scope

- Die Event-**Handler** in Goals/Diary/etc. (ziehen mit dem jeweiligen Context nach, referenziert
  als Abhängigkeit in M2/M4/…).
- Hintergrundjob für die tatsächliche Löschung nach 30 Tagen (eigenes Ticket, kann zeitlich auch
  erst mit M8 o.ä. kommen — fachlich an M1 hängend, technisch unabhängig planbar).

## Tests (Abschnitt 9)

- Domain-Unit-Tests je Invariante (E-Mail eindeutig, `PendingDeletion` kann sich nicht anmelden,
  `DisplayName` nicht leer, Refresh-Token-Rotation/Reuse-Detection).
- Value-Object-Tests (`EmailAddress`, `PasswordHash`, `DisplayName`, `UserTimeZone`, je ein
  Ungültig-Fall) + Architekturtest (kein rohes Primitive im Aggregate, kein `enum`, kein
  `datetime.utcnow()`/naives `datetime` im gesamten Pfad).
- Tagged-Union-Serialisierungstests für `Locale`, `AccountStatus`.
- Idempotenz-Test für `register`.
- Integrationstests (Testcontainers-Postgres) für jeden Endpunkt inkl. dokumentierter Fehlerfälle,
  zusätzlich manuell verifiziert per `curl` gegen die Docker-Compose-Umgebung (siehe M0).
