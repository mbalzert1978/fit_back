---
id: "0009"
title: M0: pytest + testcontainers-postgres-Fixture
status: blocked
milestone: M0
type: AFK
---

# M0: pytest + testcontainers-postgres-Fixture

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

pytest- und pytest-asyncio-Setup, sowie eine wiederverwendbare Testcontainers-Fixture fuer Postgres, die alle spaeteren Integrationstests (Abschnitt 9) nutzen koennen.

## Acceptance criteria

- [ ] uv run pytest laeuft gegen das leere Skeleton gruen (0 Tests, kein Fehler)
- [ ] Eine Beispiel-Integrationstest-Datei zeigt die Fixture in Aktion (Verbindung zu einer frisch gestarteten Testcontainers-Postgres-Instanz, Alembic-Migration wird angewendet)
- [ ] run-tests/config.json (bereits angepasst) laeuft gegen dieses Repo gruen

## Blocked by

- Blocked by [0003](0003-m0-alembic-grundgeruest-mit-7-schemas-identity-catalog-diary-recipes-goals-health-shared.md)
