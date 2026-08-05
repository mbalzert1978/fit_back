---
id: "0005"
title: M0: Shared Kernel - RFC-7807 ProblemDetails + Exception-Handler
status: closed
milestone: M0
type: AFK
---

# M0: Shared Kernel - RFC-7807 ProblemDetails + Exception-Handler

## Parent

Meilenstein [M0](docs/milestones/m0-projekt-grundgeruest.md) - siehe dort fuer vollstaendigen fachlichen
Kontext, Cross-Cutting-Check und den Bezug zu docs/Draft/BACKEND.md.

## What to build

ProblemDetails-Modell und ein FastAPI-Exception-Handler, der jeden erwarteten Domaenenfehler auf application/problem+json abbildet (Abschnitt 0.6), inkl. Validierungsfehler 400 mit gefuelltem errors-Objekt.

## Acceptance criteria

- [ ] Ein absichtlich ausgeloester Domaenenfehler liefert exakt das im Draft (Abschnitt 0.6) gezeigte JSON-Schema mit korrektem Content-Type application/problem+json
- [ ] Ein Validierungsfehler liefert 400 mit befuelltem errors-Feld
- [ ] Unit-Test pro Fehlerform (Domaenenfehler, Validierungsfehler)

## Blocked by

- Blocked by [0001](0001-m0-repo-skeleton-docker-compose-postgres-minio-app-health-endpoint-curl-smoke-test.md)

## Abschluss (2026-08-05)

Umgesetzt in PR #5 (gemerged). Keine Security-Eskalation. Branch musste zweimal auf main
nachgezogen werden (main.py/pyproject.toml/uv.lock-Konflikte durch parallel gemergte
Tickets 0002/0003/0004), siehe docs/decisions/2026-08-05-1045-... und -1110-....
