# pgsty/minio-Fork statt archiviertem minio/minio

**Entschieden:** 2026-08-05 09:56

## Was

Die Blob-Storage-Entscheidung aus
[`docs/milestones/01-technical-decisions.md`](../milestones/01-technical-decisions.md)
(„S3-kompatibel von Anfang an: MinIO lokal, S3 in Produktion") bleibt inhaltlich bestehen, aber
das konkrete Image wechselt: `docker-compose.yml` (Ticket 0001) nutzt jetzt
`pgsty/minio:RELEASE.2026-06-18T00-00-00Z` statt `minio/minio:latest`.

## Warum

Beim Umsetzen von Ticket 0001 wurde zunächst nur eine unabhängige Frage geprüft (warum ist
Postgres auf `17-alpine` statt `18-alpine` gepinnt — Antwort: Gewohnheit des Entwickler-Agenten,
korrigiert auf `18-alpine`, aktuelle stabile Major-Version seit September 2025). Dabei fiel auf,
dass MinIO nicht gepinnt war (`:latest`) — und bei der Recherche dazu ein deutlich größerer
Befund: **das offizielle `minio/minio`-Projekt ist tot.** Zeitlicher Ablauf laut Recherche:
Oktober 2025 Einstellung der öffentlichen Docker-Builds, 03.12.2025 Umstellung auf „Maintenance
Mode" (nur noch Security-Fixes, keine neuen Features), 25.04.2026 vollständige Archivierung des
GitHub-Repos (read-only). MinIO Inc. verweist seither auf das proprietäre Nachfolgeprodukt
„AIStor".

Der Stakeholder hat daraufhin entschieden: **aktiv gepflegten Fork nutzen** (`pgsty/minio`, API-
kompatibel, aktuelle Releases — zum Zeitpunkt dieser Entscheidung `RELEASE.2026-06-18T00-00-00Z`)
statt (a) das tote Original ungepflegt weiterzunutzen, (b) eine grundsätzlich andere
S3-kompatible Lösung zu evaluieren (größerer Architektur-Schnitt, hier nicht gewählt), oder
(c) die Frage auf später zu verschieben.

## Was das ausschließt / ersetzt

- Ersetzt `minio/minio:latest` durch `pgsty/minio:RELEASE.2026-06-18T00-00-00Z` in
  `docker-compose.yml` (Ticket 0001).
- Ändert nichts an der API-Anbindung (`BlobStorage`-Port, `Protocol` in
  `infrastructure/adapters/`) — der Fork ist API-kompatibel, betrifft nur das Image.
- Schließt für den Moment aus, eine grundsätzlich andere S3-kompatible Lösung (Garage, SeaweedFS
  o. Ä.) zu evaluieren — das wäre ein größerer, eigener Untersuchungs-Task, nicht Teil dieser
  Entscheidung.
- Der konkrete Fork-Tag ist ein Momentaufnahme-Pin, kein Dauerzustand — bei jedem Ticket, das
  MinIO/den Fork berührt, den aktuellen stabilen Tag neu prüfen statt diesen für alle Zeit
  fortzuschreiben (siehe auch die begleitende Versions-Policy-Entscheidung).
