# Fit-back API

Ein Backend für Fitness- und Ernährungs-Tracking, gebaut mit Python, FastAPI und PostgreSQL.

## Voraussetzungen

- Docker und Docker Compose
- oder: Python 3.14+, PostgreSQL und MinIO für die lokale Entwicklung

## Schnellstart mit Docker Compose

### Umgebung einrichten

Eine `.env` aus der Vorlage anlegen (erforderlich, bevor Docker Compose läuft):

```bash
cp .env.example .env
```

Danach in `.env` alle `CHANGEME`-Werte durch eigene Geheimnisse ersetzen. **`.env` niemals in die
Versionsverwaltung committen.**

### Dienste starten

postgres, minio und die App im Hintergrund starten:

```bash
docker compose up -d
```

Das bewirkt:
- PostgreSQL startet auf Port 5432 (erforderliche Zugangsdaten siehe `.env.example`)
- MinIO startet auf den Ports 9000 (API) und 9001 (Console)
- Die Fit-back-API wird gebaut und startet auf Port 8000

Warten, bis alle Dienste gesund sind (typischerweise 10-15 Sekunden):

```bash
docker compose ps
```

### Health-Endpunkt prüfen

Sobald die App läuft, den Health-Endpunkt mit curl testen:

```bash
curl http://localhost:8000/api/v1/health
```

Erwartete Antwort (wenn die Datenbank verbunden ist):

```json
{"status": "healthy"}
```

### Dienste stoppen

```bash
docker compose down
```

Zusätzlich die Volumes entfernen (Datenbankinhalt):

```bash
docker compose down -v
```

## Entwicklung

### Der Task-Runner

```bash
# Verfügbare Targets anzeigen
./make.ps1 help

# Abhängigkeiten installieren
./make.ps1 install

# Die App lokal starten (ohne Docker)
./make.ps1 run

# Den Compose-Stack starten
./make.ps1 compose-up

# Den Compose-Stack stoppen
./make.ps1 compose-down

# Tests ausführen (benötigt die Test-Fixture)
./make.ps1 test

# Lint- und Format-Prüfungen
./make.ps1 lint
./make.ps1 format
./make.ps1 format-check

# Alle CI-Prüfungen ausführen
./make.ps1 ci
```

### Lokales Setup ohne Docker

Wer ohne Docker arbeiten will:

1. Abhängigkeiten installieren:
   ```bash
   uv sync
   ```

2. Sicherstellen, dass PostgreSQL lokal läuft, oder die `DB_*`-Umgebungsvariablen setzen

3. Die App starten:
   ```bash
   uv run python -m src.main
   ```

4. Den Health-Endpunkt testen:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

## Projektstruktur und Architektur

Siehe [`docs/architecture.md`](docs/architecture.md) — die einzige lebende Referenz für
Verzeichnisbaum, Contexts, die maschinell erzwungene Abhängigkeitsrichtung, die erlaubten Kanäle
zwischen Contexts und die Querschnitts-Regeln. Die Stack-Entscheidungen dahinter stehen in
[`docs/milestones/01-technical-decisions.md`](docs/milestones/01-technical-decisions.md).

## API-Endpunkte

### Health-Check

- **Endpunkt:** `GET /api/v1/health`
- **Beschreibung:** Liefert den Gesundheitszustand der Anwendung und der Datenbankverbindung
- **Antwort (gesund):** `200 OK` mit `{"status": "healthy"}`
- **Antwort (ungesund):** `503 Service Unavailable` mit Fehlerdetails
