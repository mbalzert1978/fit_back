---
name: slice-shape-check
description: Check the mechanically-verifiable half of this repo's feature-slice form — every use-case package carries a Test-API and in-memory fakes, and no spec reaches past the Test-API into the domain, handler, mappers, fakes, or infrastructure. Structure only, no code judgment. Portable via config.json (globs + forbidden import fragments); required config missing ends the run with `Verdict: CONFIG ERROR`, not a silent pass. Use as a QA-Gate leg or standalone — "hat der Slice eine Test-API", "greift der Test an der Test-API vorbei", "slice shape check", "feature-slice form check".
arguments: Optional. Scope — a base branch / diff range. Defaults to the current branch's changes vs its merge-base with the default branch. Pass `--all` to sweep the whole repo instead of just the diff.
---

# Slice Shape Check

Verify that every touched use-case package has the shape
[`.rules/python/python-feature-slices.md`](../../../.rules/python/python-feature-slices.md)
prescribes, and return an objective verdict: **BLOCK** or **APPROVE**.

This covers only the part of the slice form a machine can settle — file presence and
import edges. It makes **no** judgment about code quality, naming, or whether the
domain model is any good; that stays with `review-against-rules` and
`thermo-nuclear-code-quality-review`. The point is that the cheap, objective half
never again costs an LLM review cycle — and never again silently passes.

## Verdict

**BLOCK** — at least one inspected use-case package is missing its
`adapters/test_api/` directory or the `fakes/` directory inside it, or at least one
inspected spec imports a module matching a forbidden fragment (reaching past the
Test-API).

**APPROVE** — every inspected use case carries both, and every inspected spec stays
behind the Test-API.

**Read the `Scope:` line, always.** The report states how many use cases and specs were
actually inspected. `Scope: 0 use case(s), 0 spec file(s) inspected` with
`Verdict: APPROVE` means **nothing was checked**, not that everything is correct —
this repo genuinely has zero use-case packages until the first slice lands, so a bare
`APPROVE` here would be false comfort.

## Criteria

1. **Test-API present** — every inspected `src/contexts/<ctx>/application/<use_case>/`
   contains an `adapters/test_api/` directory (`required_dirs`). The Test-API is a
   shipped part of the slice, not test scaffolding, and it lives under `adapters/`
   because it is itself an adapter onto the seam — correctness.
2. **Fakes present** — that Test-API directory contains a `fakes/` subdirectory
   (`required_dirs`). The fakes sit *inside* the Test-API, not beside it: nothing
   outside the Test-API consumes them — correctness.
3. **Specs stay behind the Test-API** — no spec under
   `src/contexts/<ctx>/specs/<use_case>/` imports a module whose dotted path contains
   any `spec_forbidden_import_fragments` entry (`.domain`, `.infrastructure`,
   `.handler`, `.fakes`, `_mapper`). Arrange runs through the Test-API, Act through the
   real request DTO, Assert against the real response union — anything else means the
   test is coupled to internals — correctness.

Directories named in `use_case_exclude_names` (`shared`, `validators`, `__pycache__`)
are not use cases and are skipped.

## External data

None — self-contained. The check needs only the repo's own git history (to resolve the
diff scope), the working tree, and `config.json`. Imports are parsed with `ast` from the
standard library; no code is executed and no external service is called.

## Process

1. **Preflight.** Read `config.json`. Every key in the script's `REQUIRED_KEYS` is
   required — if any is missing or empty, **stop** and report `Verdict: CONFIG ERROR`
   naming the missing key(s), per `_shared/validator-contract.md`
   ("`Verdict: CONFIG ERROR` abort"). No hardcoded fallback: a repo that hasn't
   configured this layout hasn't opted into the check.

2. **Resolve scope** — follows `_shared/validator-contract.md` ("Scope resolution
   (diff-scoped validators)"). Only use cases touched by the diff and specs changed by
   the diff are inspected, so pre-existing debt doesn't re-flag on every PR.

3. **Run the check.** Fully deterministic — don't eyeball it:

   ```bash
   uv run .claude/skills/slice-shape-check/scripts/check_slice_shape.py [base-ref] [--all]
   ```

   `--all` sweeps every use case and spec in the repo instead of just the diff — use it
   when auditing the whole codebase rather than gating one change.

4. **Relay.** Print the script's output verbatim, including the `Scope:` line. This
   skill doesn't re-derive or restate the check in prose.

## Output format

Whatever the script printed, verbatim:

```
Verdict: BLOCK
Scope: 2 use case(s), 3 spec file(s) inspected
- src/contexts/identity/application/register_user/: use case is missing test_api.py
- src/contexts/identity/specs/register_user/test_register_user.py: spec imports `src.contexts.identity.domain.user` — reaches past the Test-API (forbidden fragment `.domain`)
Findings: 2
```

or, on a clean pass:

```
Verdict: APPROVE
Scope: 2 use case(s), 3 spec file(s) inspected
Findings: 0
```

For a step-1 abort, the `Verdict: CONFIG ERROR` block instead, per
`_shared/validator-contract.md`.
