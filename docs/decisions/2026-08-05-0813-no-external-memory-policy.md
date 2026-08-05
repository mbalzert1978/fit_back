# No external memory mechanism — decisions live under docs/decisions/

**Decided:** 2026-08-05 08:13

## What

No persistent memory mechanism outside this repository (Claude Code's cross-session memory
system, or any other out-of-repo note-taking) is used for decisions or noteworthy changes
concerning this repository. This applies both to creating new entries and to leaving existing
ones in place — none should exist.

Decisions and noteworthy changes are instead recorded exclusively as files under this directory,
one per decision, named `YYYY-MM-DD-HHMM-<slug>.md`.

## Why

Keeps the repository the single source of truth for why things are the way they are — anyone
cloning it (or any assistant working in it in a future session) sees the full decision history
without depending on a separate, harder-to-share, harder-to-review memory store.

## What it rules out / supersedes

- A stray, unrelated `MEMORY.md` (and a sibling note file) belonging to a different, unrelated
  project had ended up committed under `.claude/projects/` in this repo — removed as part of this
  decision.
- `docs/milestones/01-technical-decisions.md` remains as-is (it documents the technical framing of
  the backend port, not a decision log) — new decisions from this point on go under
  `docs/decisions/`, not appended there.
