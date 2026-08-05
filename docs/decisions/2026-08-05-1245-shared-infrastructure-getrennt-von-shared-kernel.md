# Shared Infrastructure als eigenes Top-Level-Package, getrennt von shared_kernel

**Datum:** 2026-08-05, 12:45

## Entscheidung

`src/shared_kernel/` bleibt strikt domänen-rein (nur stdlib: `Result[T,E]`, `TimeProvider`,
`ProblemDetails`, Exceptions). Jede Infrastruktur-Abhängigkeit (SQLAlchemy-ORM-Modelle,
zukünftig Outbox-Relay-Tabellen o. Ä.), die von mehreren Contexts gemeinsam genutzt wird,
lebt stattdessen in einem eigenen, gleichrangigen Top-Level-Package `src/shared_infrastructure/`
— nicht als Unterordner von `shared_kernel` (z. B. `shared_kernel/infrastructure/`).

## Kontext

Im Rahmen des Reviews von PR #6 (Ticket 0006, Idempotency-Key-Middleware) wurde
`src/shared_kernel/db_schemas.py` (ein SQLAlchemy-ORM-Modell) bemängelt: shared_kernel enthält
mit `Result[T,E]` eindeutig domänenreinen Code, eine SQLAlchemy-Abhängigkeit direkt daneben
verstößt gegen die Regel, dass die Domäne frei von externen Belangen bleiben muss. Der erste
Fix (Verschieben nach `src/shared_kernel/infrastructure/`) wurde vom Reviewer im selben PR
erneut bemängelt — eine Unterordner-Verschachtelung unter `shared_kernel` reicht nicht, weil sie
weiterhin im selben Package liegt.

## Konsequenz für laufende und künftige Tickets

- Ticket 0006 (dieses PR): `db_schemas.py` liegt jetzt unter `src/shared_infrastructure/`.
- Ticket 0010 (Postgres-Outbox, SKIP LOCKED/LISTEN NOTIFY) braucht mit hoher Wahrscheinlichkeit
  ebenfalls ein SQLAlchemy- oder direktes-SQL-Modell für die Outbox-Tabelle — dieses Modell
  gehört von Anfang an nach `src/shared_infrastructure/`, nicht nach `src/shared_kernel/`.
- Die Middleware/Handler-Logik selbst (z. B. `idempotency.py`, das per Roh-SQL auf asyncpg
  zugreift) bleibt weiterhin in `shared_kernel/` — dort ist bereits Präzedenzfall
  `exception_handlers.py` (nutzt FastAPI), der vom Reviewer nicht bemängelt wurde. Betroffen ist
  ausschließlich das ORM-Modell/Schema selbst, nicht jeder Framework-Import in shared_kernel.
- `CLAUDE.md`s Architektur-Abschnitt nennt `src/shared_kernel/` bislang ohne diese Trennung
  explizit zu erwähnen — bei nächster inhaltlicher Überarbeitung dieses Abschnitts nachziehen.
