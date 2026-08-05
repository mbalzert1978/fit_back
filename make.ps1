#Requires -Version 5.1
<#
.SYNOPSIS
  make-style task runner for this repo (PowerShell, no GNU make needed).

.DESCRIPTION
  Every worktree under .claude/worktrees/ gets this file via git (it's tracked), so the
  same `./make.ps1 <target>` commands work identically in the main checkout and in every
  worktree. Targets mirror the commands documented in CLAUDE.md.

  Some targets depend on tooling introduced by later docs/issues/ tickets (ruff config,
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
        Description = 'Run the placeholder entrypoint (main.py)'
        Action      = { Invoke-Step 'run' { uv run python main.py } }
    }

    'test' = @{
        # Depends on docs/issues/0009 (pytest + testcontainers-postgres fixture).
        Description = 'Run the test suite (uv run pytest)'
        Action      = {
            Write-Host "==> test" -ForegroundColor Cyan
            uv run pytest
            # pytest exits 5 when zero tests are collected - a valid state for
            # tooling-only tickets (e.g. 0002/0003) that add no test files yet.
            if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 5) {
                throw "target 'test' failed with exit code $LASTEXITCODE"
            }
        }
    }

    'lint' = @{
        # Depends on docs/issues/0002 (ruff config).
        Description = 'Lint with ruff'
        Action      = { Invoke-Step 'lint' { uv run ruff check . } }
    }

    'format' = @{
        # Depends on docs/issues/0002 (ruff config).
        Description = 'Format in place with ruff'
        Action      = { Invoke-Step 'format' { uv run ruff format . } }
    }

    'format-check' = @{
        # Depends on docs/issues/0002 (ruff config).
        Description = 'Check formatting without writing changes (CI-safe)'
        Action      = { Invoke-Step 'format-check' { uv run ruff format --check . } }
    }

    'import-lint' = @{
        # Depends on docs/issues/0002 (.importlinter contract).
        Description = 'Check bounded-context import boundaries (import-linter)'
        Action      = { Invoke-Step 'import-lint' { uv run lint-imports } }
    }

    'migrate' = @{
        # Depends on docs/issues/0003 (Alembic baseline).
        Description = 'Apply database migrations (alembic upgrade head)'
        Action      = { Invoke-Step 'migrate' { uv run alembic upgrade head } }
    }

    'compose-up' = @{
        # Depends on docs/issues/0001 (docker-compose.yml: postgres, minio, app).
        Description = 'Start postgres/minio/app via docker compose (detached)'
        Action      = { Invoke-Step 'compose-up' { docker compose up -d } }
    }

    'compose-down' = @{
        # Depends on docs/issues/0001 (docker-compose.yml).
        Description = 'Stop and remove the docker compose stack'
        Action      = { Invoke-Step 'compose-down' { docker compose down } }
    }

    'ci' = @{
        Description = 'lint + format-check + import-lint + test, in that order'
        Action      = {
            Invoke-Target 'lint'
            Invoke-Target 'format-check'
            Invoke-Target 'import-lint'
            Invoke-Target 'test'
        }
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
