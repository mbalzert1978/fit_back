---
id: "0001"
title: M0: Repo-Skeleton, Docker Compose (postgres/minio/app), Health-Endpoint, curl-Smoke-Test
status: open
milestone: M0
type: AFK
---

# M0: Repo-Skeleton, Docker Compose (postgres/minio/app), Health-Endpoint, curl-Smoke-Test

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

Grundlegende Ordnerstruktur gemaess docs/milestones/01-technical-decisions.md (src/contexts/, src/api/, src/shared_kernel/), ein docker-compose.yml mit Services postgres, minio und app (FastAPI via uvicorn), ein Dockerfile fuer den app-Service, sowie ein einfacher Health-Endpoint GET /api/v1/health, der 200 liefert sobald die App gegen Postgres verbunden ist. Ziel: docker compose up bringt alles hoch, curl gegen den Health-Endpoint antwortet.

## Acceptance criteria

- [ ] docker compose up startet postgres, minio und app fehlerfrei
- [ ] GET /api/v1/health liefert 200 (verifiziert per curl gegen den laufenden Container)
- [ ] src/contexts/, src/api/, src/shared_kernel/ existieren als leere, importierbare Pakete
- [ ] README dokumentiert den docker compose up + curl Workflow als primaeren manuellen Testweg

## Blocked by

None - can start immediately
