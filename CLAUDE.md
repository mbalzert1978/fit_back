# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Where things live

- [`docs/Draft/BACKEND.md`](docs/Draft/BACKEND.md) — the full functional specification, originally
  written for ASP.NET Core/C#. This repo is **Python 3.14**, so the spec is ported, not
  implemented verbatim. Read [`docs/milestones/01-technical-decisions.md`](docs/milestones/01-technical-decisions.md)
  before assuming any technology choice — it records every decision made to adapt the spec to this
  stack (web framework, persistence, background jobs, blob storage, cross-context communication,
  repo layout) and is the tie-breaker whenever the spec and this stack appear to disagree.
- [`docs/milestones/`](docs/milestones/) — the milestone breakdown (M0–M8) derived from the spec.
- [`docs/issues/`](docs/issues/) — tracer-bullet issues implementing the milestones, gated by the
  `verify-issue-breakdown` skill before publish. Implement from the matching issue, not directly
  from `docs/Draft/BACKEND.md` — the issue already resolves the spec against this repo's stack and
  layout. Issue progress lives in each issue's own frontmatter (`issue-status` skill), not in a
  central changelog.
- [`.rules/`](.rules/) — coding standards (`common/` language-agnostic, `python/` Python-specific).
  Read `.rules/python/README.md` first — it lists reading order and how conflicts between files
  resolve.
- [`docs/decisions/`](docs/decisions/) — see "Decisions and memory policy" below.

## Commands

`make.ps1` at the repo root is the canonical task runner (PowerShell, no GNU make required) — it
is tracked in git, so the same `./make.ps1 <target>` commands work identically in the main
checkout and in every worktree under `.claude/worktrees/`. Run `./make.ps1 help` for the target
list; `./make.ps1 ci` runs lint + format-check + import-lint + test.

Prefer the project skill library under `.claude/skills/` (e.g. `to-issues`,
`verify-issue-breakdown`, `review-against-rules`, `qa-check`, `lint-and-format-check`,
`run-tests`) over ad-hoc commands for planning, review, lint, and test workflows — several
`config.json` files there are already wired to this repo's Python/uv/ruff/pytest stack.

## Architecture

**Modular monolith, one Bounded Context per module**, per
[`docs/milestones/01-technical-decisions.md`](docs/milestones/01-technical-decisions.md):

```
src/contexts/<context>/domain/            # aggregates, value objects, domain ports (Protocol) — stdlib only
src/contexts/<context>/application/<use_case>/   # one folder per use case: command, handler, mappers, validators
src/contexts/<context>/infrastructure/    # SQLAlchemy models/repositories, external adapters
src/contexts/<context>/tests/<use_case>/  # tests through the use case's public test API only
src/api/<context>/                        # FastAPI routers — HTTP <-> application DTOs only
src/shared_kernel/                        # Result[T,E], TimeProvider, RFC-7807 ProblemDetails,
                                           # Idempotency-Key middleware, IUserOwned, UUIDv7, Outbox
```

Contexts: `identity`, `catalog`, `diary`, `recipes`, `goals`, `health_sync` — one PostgreSQL schema
each, no context ever queries another context's tables.

**Cross-context communication is deliberately constrained** (goal: contexts can be extracted into
separate services later without rewriting their logic):
- Fire-and-forget reactions (e.g. `UserRegistered` triggering a default Goals profile or Diary's
  standard meal slots) go through a **Postgres-backed outbox** (`SELECT ... FOR UPDATE SKIP
  LOCKED` + `LISTEN/NOTIFY`), never a direct in-process event dispatch.
- Synchronous calls where the caller needs an immediate result (e.g. Recipes calling into Diary)
  go through a **consumer-owned `Protocol` port** — the calling context defines the narrow
  interface it needs, and the port implementation calls the target context's application service
  in-process, never its domain/handler/ORM code directly.

**Test pyramid** has an explicit Contract-Tests layer for exactly these two boundary kinds, sitting
between Domain-Unit-Tests and Integration-Tests — see
[`docs/milestones/02-test-pyramide.md`](docs/milestones/02-test-pyramide.md) before writing tests
that cross a context boundary.

Cross-cutting rules that apply to every context (nutrient values always per 100g, rounding is
presentation-only, RFC-7807 error format, JWT auth, no primitive obsession, tagged unions instead
of enums, `DateTimeOffset`-only timestamps, optimistic concurrency via `RowVersion`/`If-Match`) are
specified in `docs/Draft/BACKEND.md`, section 0, and implemented once in `shared_kernel` rather
than per context.

## Decisions and memory policy

**No external/persistent memory mechanism is used for this repository** — not Claude Code's
cross-session memory system, not any other out-of-repo note-taking. This applies both to creating
new entries and to leaving any that already exist; none should exist here.

Decisions and noteworthy changes are recorded **exclusively** under [`docs/decisions/`](docs/decisions/),
one file per decision, named `YYYY-MM-DD-HHMM-<slug>.md`, dated and timestamped at the moment the
decision is made. This is binding for all future sessions working in this repository.
