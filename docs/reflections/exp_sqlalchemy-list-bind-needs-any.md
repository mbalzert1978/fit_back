---
schema_version: 1
name: sqlalchemy-list-bind-needs-any
description: SQLAlchemy text() expandiert eine Python-list, die an einen einzelnen benannten Parameter gebunden wird, nicht automatisch zu IN(...) - mit asyncpg fuehrt das zu DataError
type: project
frequency: 1
last_triggered: 2026-08-05
decay_eligible: false
---

`text("... WHERE col IN (:param)")` mit `{"param": ["a", "b", "c"]}` funktioniert nicht -
SQLAlchemy reicht die Python-list unveraendert als EIN Bind-Argument durch, asyncpg erwartet dort
einen Skalar und wirft `DataError: invalid input for query argument $1 (expected str, got list)`.

**Why:** Ticket 0009s Schema-Existenz-Test (`test_alembic_migration_applied`) nutzte genau dieses
Muster, um gegen eine Menge von Schema-Namen zu pruefen - erst nach dem Fund schlug der eigentliche
inhaltliche Fehler (fehlende Schemas) durch, vorher verdeckte der `DataError` ihn komplett.
**How to apply:** Fuer eine Liste von Werten gegen eine einzelne Spalte in Postgres/asyncpg:
`WHERE col = ANY(:param)` verwenden (nimmt eine Liste direkt als Array-Parameter entgegen), nicht
`IN (:param)`. Alternativ SQLAlchemy's `bindparam(..., expanding=True)`, wenn `IN` semantisch
gebraucht wird.
