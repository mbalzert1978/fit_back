Implementiere Ticket 0001 vollständig im aktuellen Arbeitsverzeichnis (dedizierter Git-Worktree für dieses Ticket, Branch `0001-repo-skeleton`).

# M0: Repo-Skeleton, Docker Compose (postgres/minio/app), Health-Endpoint, curl-Smoke-Test

## Kontext
- Meilenstein M0 (`docs/milestones/m0-projekt-grundgeruest.md`) — vollständiger fachlicher Kontext, Cross-Cutting-Check, Bezug zu `docs/Draft/BACKEND.md`.
- Technischer Rahmen (Stack, Repo-Layout): `docs/milestones/01-technical-decisions.md`.
- Coding-Standards: zuerst `.rules/python/README.md` lesen (Leseweg + Konfliktauflösung), dann `.rules/common/` und `.rules/python/`.
- Repo ist Python 3.14, Paketmanager `uv`.

## Was zu bauen ist
1. Grundlegende Ordnerstruktur gemäß `docs/milestones/01-technical-decisions.md` anlegen: `src/contexts/`, `src/api/`, `src/shared_kernel/` — jeweils als leere, importierbare Python-Pakete (`__init__.py`).
2. `docker-compose.yml` im Repo-Root mit drei Services: `postgres`, `minio`, `app` (FastAPI über `uvicorn`).
3. `Dockerfile` für den `app`-Service.
4. Health-Endpoint `GET /api/v1/health`, der `200` liefert, sobald die App erfolgreich gegen Postgres verbunden ist.
5. `make.ps1` im Repo-Root: die bereits vorhandenen Platzhalter-Targets `run`, `compose-up`, `compose-down` so weit nötig anpassen, damit sie gegen den neuen `docker-compose.yml`/die neue App tatsächlich funktionieren (keine neuen Targets erfinden, nur bestehende funktionsfähig machen).
6. `README.md`: den `docker compose up` + `curl`-Workflow als primären manuellen Testweg dokumentieren.

## Akzeptanzkriterien (alle müssen erfüllt sein)
- [ ] `docker compose up` startet `postgres`, `minio` und `app` fehlerfrei.
- [ ] `GET /api/v1/health` liefert `200` — verifiziert per `curl` gegen den laufenden Container (im Rahmen der Umsetzung tatsächlich ausführen und die Ausführung/Ausgabe kurz belegen, nicht nur behaupten).
- [ ] `src/contexts/`, `src/api/`, `src/shared_kernel/` existieren als leere, importierbare Pakete.
- [ ] `README.md` dokumentiert den `docker compose up` + `curl`-Workflow als primären manuellen Testweg.

## Abgrenzung — NICHT tun
- Keine fachliche Logik über den Health-Endpoint hinaus implementieren (keine Contexts/Aggregate/Use-Cases — das sind spätere Tickets).
- Keinen `git push` und keinen PR erstellen — das übernimmt eine spätere Pipeline-Stufe.
- Keine neuen `make.ps1`-Targets über die bestehenden Platzhalter hinaus einführen.

## Abschluss
- Änderungen auf dem aktuellen Branch (`0001-repo-skeleton`) committen (`git add` + `git commit`), keine weiteren Branches anlegen.
- **Fertig**, wenn alle vier Akzeptanzkriterien oben erfüllt und im Commit nachvollziehbar sind (z. B. curl-Ausgabe in der Commit-Message oder im PR-Text der nächsten Stufe erwähnt).

## Blocked by
Keine Abhängigkeiten — kann sofort gestartet werden.
