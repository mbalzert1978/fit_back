---
id: "0003"
title: M0: Alembic-Grundgeruest mit 7 Schemas (identity/catalog/diary/recipes/goals/health/shared)
status: blocked
milestone: M0
type: AFK
---

# M0: Alembic-Grundgeruest mit 7 Schemas (identity/catalog/diary/recipes/goals/health/shared)

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Alembic-Setup mit einer Baseline-Migration je DbSchema aus Abschnitt 0 (BACKEND.md Zeile 18): identity, catalog, diary, recipes, goals, health, shared. Jedes Schema wird als eigenes Postgres-Schema angelegt (CREATE SCHEMA), noch ohne fachliche Tabellen.

## Acceptance criteria

- [ ] alembic upgrade head legt alle 7 Schemas in Postgres an
- [ ] alembic downgrade base entfernt sie wieder sauber
- [ ] Schema-Namen sind exakt wie im Draft benannt (identity, catalog, diary, recipes, goals, health, shared)

## Blocked by

- Blocked by [0001](0001-m0-repo-skeleton-docker-compose-postgres-minio-app-health-endpoint-curl-smoke-test.md)
