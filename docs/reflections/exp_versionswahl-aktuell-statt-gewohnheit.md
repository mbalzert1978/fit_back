---
schema_version: 1
name: versionswahl-aktuell-statt-gewohnheit
description: Bei jeder Versionswahl (Docker-Images, Dependencies) die aktuelle stabile Version verifizieren statt einer aus Trainingsdaten naheliegenden aelteren Version
type: feedback
frequency: 1
last_triggered: 2026-08-05
decay_eligible: false
---

Bei jeder expliziten Versionswahl (Docker-Image-Major-Version, Package-Version)
die tatsaechlich aktuelle stabile Version verwenden — nicht die aus
Trainingsdaten/Gewohnheit naheliegende aeltere Version. Gleichzeitig NIE einen
bloßen `:latest`-Tag verwenden (Reproduzierbarkeit) — „aktuell" heißt explizit
gepinnt auf die zum Zeitpunkt der Umsetzung aktuelle Version, nicht „beweglich".

**Why:** Der Entwickler-Agent pinnte `postgres:17-alpine` statt der seit
September 2025 aktuellen Major-Version 18, und `minio/minio:latest` ungepinnt
auf einem inzwischen archivierten Projekt. Der Nutzer korrigierte das explizit
und formulierte eine generelle Vorgabe. Details:
[docs/decisions/2026-08-05-1000-aktuelle-versionen-statt-gewohnheit.md](../decisions/2026-08-05-1000-aktuelle-versionen-statt-gewohnheit.md).

**How to apply:** Vor jeder expliziten Versionsangabe in Docker-Compose/Dockerfile
oder Dependency-Deklaration, wo die Major-Version nicht offensichtlich ist, kurz
per Websuche verifizieren statt zu raten — insbesondere bei Basis-Images.
