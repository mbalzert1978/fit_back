#Requires -Version 5.1
<#
.SYNOPSIS
  make-style task runner for this repo (PowerShell, no GNU make needed).

.DESCRIPTION
  Every worktree under .claude/worktrees/ gets this file via git (it's tracked), so the
  same `./make.ps1 <target>` commands work identically in the main checkout and in every
  worktree. Targets mirror the commands documented in CLAUDE.md.

  Some targets depend on tooling introduced by later tickets (ruff config,
  import-linter contract, docker-compose.yml, alembic setup) and will fail with the
  underlying tool's own error until that ticket lands - see the comment on each target.

.EXAMPLE
  ./make.ps1 test
  ./make.ps1 lint format-check
  ./make.ps1 ci
#>
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Targets
)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function Invoke-Step {
    param([string]$Name, [scriptblock]$Action)
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
        throw "target '$Name' failed with exit code $LASTEXITCODE"
    }
}

$targetTable = [ordered]@{
    'help' = @{
        Description = 'List available targets (default when none given)'
        Action      = {
            Write-Host "Targets:`n"
            foreach ($key in $targetTable.Keys) {
                '{0,-16} {1}' -f $key, $targetTable[$key].Description
            }
        }
    }

    'install' = @{
        Description = 'Sync the uv-managed virtualenv from pyproject.toml/uv.lock'
        Action      = { Invoke-Step 'install' { uv sync --all-extras } }
    }

    'run' = @{
        Description = 'Run the API entrypoint (src/main.py)'
        Action      = { Invoke-Step 'run' { uv run python -m src.main } }
    }

    'test' = @{
        # Depends on issue #49 (pytest + testcontainers-postgres fixture).
        Description = 'Run the test suite (uv run pytest)'
        Action      = {
            Write-Host "==> test" -ForegroundColor Cyan
            uv run pytest
            # pytest exits 5 when zero tests are collected - a valid state for
            # tooling-only tickets (e.g. 0002/0003) that add no test files yet.
            if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 5) {
                throw "target 'test' failed with exit code $LASTEXITCODE"
            }
            $global:LASTEXITCODE = 0
        }
    }

    'lint' = @{
        # Depends on issue #42 (ruff config).
        Description = 'Lint with ruff'
        Action      = { Invoke-Step 'lint' { uv run ruff check . } }
    }

    'format' = @{
        # Depends on issue #42 (ruff config).
        Description = 'Format in place with ruff'
        Action      = { Invoke-Step 'format' { uv run ruff format . } }
    }

    'format-check' = @{
        # Depends on issue #42 (ruff config).
        Description = 'Check formatting without writing changes (CI-safe)'
        Action      = { Invoke-Step 'format-check' { uv run ruff format --check . } }
    }

    'typecheck' = @{
        # Issue #97: ruff prueft keine Typen. `ty` (Astral) ist der Typechecker,
        # konfiguriert samt eingefrorener Baseline in pyproject.toml.
        Description = 'Typecheck src/ and tests/ with ty'
        Action      = { Invoke-Step 'typecheck' { uv run ty check src tests } }
    }

    'import-lint' = @{
        # Depends on issue #42 (.importlinter contract).
        Description = 'Check bounded-context import boundaries (import-linter)'
        Action      = { Invoke-Step 'import-lint' { uv run lint-imports } }
    }

    'complexity' = @{
        # complexipy misst kognitive Komplexitaet je Funktion und faellt ab Wert 15.
        # Per uvx statt als Projekt-Dependency - das Werkzeug prueft den Code, es
        # gehoert nicht zu seiner Laufzeit.
        Description = 'Check cognitive complexity per function, src/ and tests/ (complexipy)'
        Action      = { Invoke-Step 'complexity' { uvx complexipy -f src tests } }
    }

    'migrate' = @{
        # Depends on issue #43 (Alembic baseline). "heads" (plural) is
        # required, not "head" - each of the 7 schemas is its own independent
        # branch/head in this multi-schema Alembic layout.
        Description = 'Apply database migrations (alembic upgrade heads)'
        Action      = { Invoke-Step 'migrate' { uv run alembic upgrade heads } }
    }

    'compose-up' = @{
        # Depends on issue #41 (docker-compose.yml: postgres, minio, app).
        Description = 'Start postgres/minio/app via docker compose (detached)'
        Action      = { Invoke-Step 'compose-up' { docker compose up -d } }
    }

    'compose-down' = @{
        # Depends on issue #41 (docker-compose.yml).
        Description = 'Stop and remove the docker compose stack'
        Action      = { Invoke-Step 'compose-down' { docker compose down } }
    }

    'claude-doctor' = @{
        # The check itself is Python (scripts/claude_doctor.py) so it stays runnable
        # on machines without pwsh - see docs/claude/README.md.
        Description = 'Check the Claude setup: external tools and hook references'
        Action      = { Invoke-Step 'claude-doctor' { uv run --script scripts/claude_doctor.py } }
    }

    'ci' = @{
        Description = 'lint + format-check + typecheck + import-lint + complexity + test, in that order'
        Action      = {
            Invoke-Target 'lint'
            Invoke-Target 'format-check'
            Invoke-Target 'typecheck'
            Invoke-Target 'import-lint'
            Invoke-Target 'complexity'
            Invoke-Target 'test'
        }
    }

    'all' = @{
        # Alias only - `all` is the name GNU make users reach for first. It stays a
        # pure forward to 'ci' so the two can never drift apart.
        Description = 'Alias for ci'
        Action      = { Invoke-Target 'ci' }
    }
}

function Invoke-Target {
    param([string]$Name)
    if (-not $targetTable.Contains($Name)) {
        Write-Error "unknown target '$Name'. Run './make.ps1 help' for the list."
        exit 1
    }
    & $targetTable[$Name].Action
}

if (-not $Targets -or $Targets.Count -eq 0) {
    $Targets = @('help')
}

foreach ($t in $Targets) {
    Invoke-Target $t
}
