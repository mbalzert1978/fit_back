# Policy: aktuelle stabile Versionen statt gewohnheitsbedingter älterer Defaults

**Entschieden:** 2026-08-05 10:00

## Was

Für jede Version-Wahl in diesem Projekt (Docker-Image-Tags, Python-Package-Versionen, sonstige
Tool-/Dependency-Versionen) gilt ab sofort: **die aktuelle stabile Version verwenden, nicht eine
ältere, aus Gewohnheit/Trainingsdaten naheliegende Version.** „Aktuell" heißt die neueste stabile
Release zum Zeitpunkt der Umsetzung — nicht der literale `:latest`-Docker-Tag (der bleibt aus
Reproduzierbarkeitsgründen weiterhin tabu, siehe unten); jede Version wird explizit gepinnt.

**Konkret für die Pipeline:** Entwickler-Agenten (Schritt „Entwicklung" der Pipeline aus
`2026-08-05-0839-implementation-pipeline-and-wave-1.md`) bekommen diese Vorgabe ab sofort explizit
im Task-Prompt mit, nicht nur implizit über `.rules/`. Wo eine Versionswahl nicht offensichtlich
ist (z. B. Major-Version eines Basis-Images), im Zweifel kurz per Websuche verifizieren statt zu
raten.

## Warum

Beim Umsetzen von Ticket 0001 hat der Entwickler-Agent `postgres:17-alpine` gepinnt, obwohl
PostgreSQL 18 seit September 2025 die aktuelle stabile Major-Version ist — reines Trainingsdaten-
/Gewohnheits-Artefakt, keine bewusste Entscheidung (z. B. Kompatibilitätsgrund). Der Stakeholder
hat das explizit korrigiert und als generelle Vorgabe formuliert: „heute bitte latest versions von
allen verwenden, nicht gewohnheitsbedingt nicht die neuste Version nutzen — das gilt vor allem für
unsere Dependencies."

**Wichtige Klarstellung, die dabei nicht verloren gehen darf:** „aktuelle Version verwenden" ist
NICHT dasselbe wie „literalen `:latest`-Tag verwenden". Der zweite Postgres-Fund in derselben
Prüfung war ein `minio/minio:latest`-Tag ohne Pin — das bleibt weiterhin falsch, unabhängig von
dieser Policy: `:latest` ist nicht reproduzierbar (liefert in sechs Monaten ein anderes Image als
heute) und genau deswegen bereits in `.rules/` bzw. gängiger Praxis vermieden. Diese Policy heißt
also: **den aktuellen Stand explizit pinnen**, nicht „immer den beweglichen `latest`-Tag
verwenden".

Bei Python-Packages via `uv`/`pyproject.toml` ist das meist bereits automatisch der Fall (`>=`-
Untergrenzen ohne Obergrenze lassen `uv sync`/`uv.lock` ohnehin die jeweils aktuelle kompatible
Version auflösen, siehe `uv.lock` von Ticket 0001: `fastapi==0.141.1`, `uvicorn==0.52.1`,
`asyncpg==0.31.0` — alles aktuell). Der Gewohnheits-Fehler trat konkret bei Docker-Image-Tags auf,
wo eine Major-Version explizit im Klartext gewählt wird statt über einen Resolver.

## Was das ausschließt / ersetzt

- Schließt aus, dass ich oder ein Entwickler-Agent eine Versionswahl unreflektiert aus
  Trainingsdaten/Gewohnheit trifft, ohne kurz zu prüfen, ob es eine neuere stabile Version gibt.
- Ändert nichts an der bestehenden Pin-Pflicht (kein `:latest`-Tag) — verschärft sie eher: sowohl
  „nicht ungepinnt" als auch „nicht auf eine veraltete Version gepinnt".
- Gilt projektweit und rückwirkend für bereits laufende Tickets (0001 wurde entsprechend
  korrigiert: `postgres:18-alpine`, `pgsty/minio:RELEASE.2026-06-18T00-00-00Z` statt
  `minio/minio:latest`), nicht nur für neue.
