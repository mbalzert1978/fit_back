---
id: "0002"
title: M0: ruff-Konfiguration + import-linter-Contract + Lint-CI-Schritt
status: open
milestone: M0
type: AFK
---

# M0: ruff-Konfiguration + import-linter-Contract + Lint-CI-Schritt

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

pyproject.toml um ruff-Konfiguration ergaenzen (inkl. ANN-Regelsatz, siehe .rules/python/README.md: kein mypy/pyright). .importlinter-Contract-Datei, die verbietet, dass ein Bounded Context (src/contexts/<a>) aus einem anderen Context (src/contexts/<b>) importiert, ausser ueber dessen application/-Schicht. Lint-CI-Schritt (ruff check, ruff format --check, import-linter) laeuft als ein Kommando.

## Acceptance criteria

- [ ] ruff check . und ruff format --check . laufen fehlerfrei gegen das leere Skeleton
- [ ] import-linter (uv run lint-imports) laeuft und schlaegt fehl, wenn ein Testimport gegen die Contract-Regel verstoesst (durch einen bewussten Testverstoss verifiziert und wieder entfernt)
- [ ] lint-and-format-check/config.json (bereits angepasst) laeuft gegen dieses Repo gruen

## Blocked by

- Blocked by [0001](0001-m0-repo-skeleton-docker-compose-postgres-minio-app-health-endpoint-curl-smoke-test.md)
