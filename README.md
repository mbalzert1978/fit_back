# Fit-back API

A fitness and nutrition tracking backend built with Python, FastAPI, and PostgreSQL.

## Prerequisites

- Docker and Docker Compose
- or: Python 3.14+, PostgreSQL, and MinIO for local development

## Quick Start with Docker Compose

### Environment Setup

Create a `.env` file from the template (required before running Docker Compose):

```bash
cp .env.example .env
```

Then edit `.env` and replace all `CHANGEME` values with your own secrets. **Never commit `.env` to version control.**

### Start the Services

Start postgres, minio, and the app in detached mode:

```bash
docker compose up -d
```

This will:
- Start PostgreSQL on port 5432 (see `.env.example` for required credentials)
- Start MinIO on ports 9000 (API) and 9001 (Console)
- Build and start the Fit-back API on port 8000

Wait for all services to be healthy (typically 10-15 seconds):

```bash
docker compose ps
```

### Verify the Health Endpoint

Once the app is running, test the health endpoint with curl:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response (if database is connected):

```json
{"status": "healthy"}
```

### Stop the Services

```bash
docker compose down
```

To also remove volumes (database data):

```bash
docker compose down -v
```

## Development

### Using the Make Task Runner

```bash
# View available targets
./make.ps1 help

# Install dependencies
./make.ps1 install

# Run the app locally (without Docker)
./make.ps1 run

# Start the compose stack
./make.ps1 compose-up

# Stop the compose stack
./make.ps1 compose-down

# Run tests (requires test fixture)
./make.ps1 test

# Lint and format checks
./make.ps1 lint
./make.ps1 format
./make.ps1 format-check

# Run all CI checks
./make.ps1 ci
```

### Local Development Setup

If you prefer to run without Docker:

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Ensure PostgreSQL is running locally or set DB_* environment variables

3. Run the app:
   ```bash
   uv run python -m src.main
   ```

4. Test the health endpoint:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

## Project Structure

```
src/
├── contexts/          # Bounded contexts (one per domain module)
├── api/              # HTTP API layer (FastAPI routers)
└── shared_kernel/    # Cross-cutting primitives (Result, UUID, etc.)
```

## API Endpoints

### Health Check

- **Endpoint:** `GET /api/v1/health`
- **Description:** Returns the health status of the application and database connection
- **Response (healthy):** `200 OK` with `{"status": "healthy"}`
- **Response (unhealthy):** `503 Service Unavailable` with error details

## Architecture

Fit-back follows a modular monolith architecture with bounded contexts. Each context owns its database schema and communicates with other contexts through either:
- Fire-and-forget reactions via a Postgres-backed outbox
- Synchronous calls through consumer-owned Protocol ports

See `docs/milestones/01-technical-decisions.md` for detailed architecture decisions.
