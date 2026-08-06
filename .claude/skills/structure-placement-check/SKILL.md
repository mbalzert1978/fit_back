---
name: structure-placement-check
description: Flag changed test files that live outside this repo's configured test-root prefixes (e.g. a stray top-level `tests/` mirror tree, or a test dropped straight into a domain/application/infrastructure folder) — a purely mechanical file-*path* check, no code content read. Portable across repos via config.json (`test_file_patterns`, `test_root_prefixes`); required config missing ends the run with `Verdict: CONFIG ERROR`, not a silent pass. Use as the cheap, objective first gate before any content-level review — "liegen die Tests am richtigen Ort", "test file placement check", "structural placement check before the QA-Gate".
arguments: Optional. Scope — a base branch / diff range. Defaults to the current branch's changes vs its merge-base with the default branch when omitted.
---

# Structure Placement Check

Verify that every changed test file lives under one of this repo's configured
test-root prefixes, and return an objective verdict: **BLOCK** or **APPROVE**.

This check exists to catch the cheapest, most objective class of structural drift
*before* an expensive content-level review runs — a misplaced test file needs zero
judgment to spot, so it shouldn't cost a full LLM review cycle to catch. It checks
**only** file location, never file content — a perfectly-written test in the wrong
place is still a finding here, and a badly-written test in the right place is not.

## Verdict

**BLOCK** — at least one changed file matches a configured test-file naming pattern
(`test_file_patterns`) but its path doesn't match any configured test-root prefix
(`test_root_prefixes`).

**APPROVE** — every changed test file matches at least one configured prefix (this
includes the case where no changed file looks like a test file at all).

## Criteria

1. **Test co-location** — every changed file whose name matches `test_file_patterns`
   (e.g. `test_*.py`) has a path starting with one of `test_root_prefixes` — checked
   by string-prefix match (with `*` wildcarding one path segment, e.g.
   `src/contexts/*/tests/*/`), not by any judgment call — correctness.

`exempt_file_names` (optional) lists file names that merely *look* like test files
but are shipped parts of a slice and therefore judged by their own rules. In this
repo that is `test_api.py`: the public Test-API of a use case is an artifact of the
slice and belongs inside `application/<use_case>/`, never under a test root — see
`.rules/python/python-feature-slices.md`, "Die Test-API ist Teil des Slice". Whether
each use case actually *has* one is `slice-shape-check`'s job, not this check's.

## External data

None — self-contained. The check needs only the repo's own git history (to resolve
the diff scope) and `config.json`; it reads no file content and calls no external
service.

## Process

1. **Preflight.** Read `config.json`. Both `test_file_patterns` and
   `test_root_prefixes` are required — if either is missing or empty, **stop** and
   report `Verdict: CONFIG ERROR` naming the missing key(s), per
   `_shared/validator-contract.md` ("`Verdict: CONFIG ERROR` abort"). Don't fall back
   to a hardcoded default pattern; a repo that hasn't configured this convention
   hasn't opted into the check.

2. **Resolve scope** — follows `_shared/validator-contract.md` ("Scope resolution
   (diff-scoped validators)"): the current branch's changes vs its merge-base with
   the default branch, or an explicit base ref.

3. **Run the check.** This is fully deterministic, so don't eyeball it:

   ```bash
   uv run .claude/skills/structure-placement-check/scripts/check_placement.py [base-ref]
   ```

   It lists every changed file matching a `test_file_patterns` glob whose path
   doesn't start with any `test_root_prefixes` entry, and prints `Verdict:` +
   `Findings: <n>` per `_shared/validator-contract.md`.

4. **Relay.** Print the script's output verbatim — this skill doesn't re-derive or
   restate the check in prose.

## Output format

Whatever the script printed, verbatim:

```
Verdict: BLOCK
Scope: 12 changed file(s), 3 test file(s) inspected
- tests/shared_kernel/i18n/test_middleware.py: test file is outside every configured test root (src/*/tests/, src/contexts/*/tests/*/)
Findings: 1
```

or, on a clean pass:

```
Verdict: APPROVE
Scope: 42 changed file(s), 1 test file(s) inspected
Findings: 0
```

The `Scope:` line is not decoration: without it, "nothing found" reads exactly like
"nothing checked" (`docs/reflections/exp_gruenes-gate-ohne-scope-angabe.md`).

For a step-1 abort, the `Verdict: CONFIG ERROR` block instead, per
`_shared/validator-contract.md`.
