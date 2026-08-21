# make-style task runner for this repo, GNU make edition.
#
# Mirrors ./make.ps1 target for target, for machines without pwsh. The
# PowerShell version stays the one CLAUDE.md points at; when a target changes,
# it changes in both files or the two drift apart.
#
#   make test
#   make lint format-check
#   make ci

.DEFAULT_GOAL := help
SHELL := /bin/sh

.PHONY: help install run test lint format format-check import-lint complexity \
        migrate compose-up compose-down claude-doctor ci all

say = @printf '==> %s\n' $(1)

help: ## List available targets (default when none given)
	@printf 'Targets:\n\n'
	@grep -hE '^[a-z][a-z-]*:.*## ' $(MAKEFILE_LIST) \
		| sed -e 's/:.*## /|/' \
		| awk -F'|' '{ printf "%-16s %s\n", $$1, $$2 }'

install: ## Sync the uv-managed virtualenv from pyproject.toml/uv.lock
	$(call say,install)
	uv sync --all-extras

run: ## Run the API entrypoint (src/main.py)
	$(call say,run)
	uv run python -m src.main

# Depends on issue #49 (pytest + testcontainers-postgres fixture).
test: ## Run the test suite (uv run pytest)
	$(call say,test)
	@uv run pytest; status=$$?; \
		[ $$status -eq 0 ] || [ $$status -eq 5 ] || exit $$status
# pytest exits 5 when zero tests are collected - a valid state for tooling-only
# tickets (e.g. 0002/0003) that add no test files yet.

# Depends on issue #42 (ruff config).
lint: ## Lint with ruff
	$(call say,lint)
	uv run ruff check .

format: ## Format in place with ruff
	$(call say,format)
	uv run ruff format .

format-check: ## Check formatting without writing changes (CI-safe)
	$(call say,format-check)
	uv run ruff format --check .

# Depends on issue #42 (.importlinter contract).
import-lint: ## Check bounded-context import boundaries (import-linter)
	$(call say,import-lint)
	uv run lint-imports

# Run via uvx rather than as a project dependency - the tool checks the code, it
# is not part of the code's runtime. complexipy fails a function from 15 up.
complexity: ## Check cognitive complexity per function (complexipy)
	$(call say,complexity)
	uvx complexipy -f src

# Depends on issue #43 (Alembic baseline). "heads" (plural) is required, not
# "head" - each of the 7 schemas is its own independent branch/head in this
# multi-schema Alembic layout.
migrate: ## Apply database migrations (alembic upgrade heads)
	$(call say,migrate)
	uv run alembic upgrade heads

# Depends on issue #41 (docker-compose.yml: postgres, minio, app).
compose-up: ## Start postgres/minio/app via docker compose (detached)
	$(call say,compose-up)
	docker compose up -d

compose-down: ## Stop and remove the docker compose stack
	$(call say,compose-down)
	docker compose down

# The check itself is Python (scripts/claude_doctor.py) so it stays runnable on
# machines without pwsh - see docs/claude/README.md.
claude-doctor: ## Check the Claude setup: external tools and hook references
	$(call say,claude-doctor)
	uv run --script scripts/claude_doctor.py

ci: lint format-check import-lint complexity test ## lint + format-check + import-lint + complexity + test, in that order

# Alias only - `all` is the name GNU make users reach for first. It stays a pure
# forward to 'ci' so the two can never drift apart.
all: ci ## Alias for ci
