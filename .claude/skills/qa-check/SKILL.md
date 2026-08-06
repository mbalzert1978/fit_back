---
name: qa-check
description: Run the repo's test suite via the canonical `run-tests` skill, and optionally flag any changed production unit whose configured test location didn't change alongside it. The coverage check is toggleable via `config.json` so this skill still makes sense in a repo with a different test topology; the production-unit-to-test-location mapping is configured, never assumed. Returns PASS/FAIL plus a `Findings: <n>` count. Use as one leg of a validator loop, or standalone when checking whether tests kept up with a change — "sind Tests gruen", "fehlt ein Spec-Update", "QA-Check", "did the tests keep up with this change".
arguments: Optional. Base ref to diff against for the coverage-gap check (default: same resolution as `thermo-nuclear-code-quality-review`'s size pass — `origin/HEAD`/`origin/main`/`main` in that order).
---

# QA Check

Two checks: the test suite must be green (mandatory), and every changed production unit
should have a change in its configured test location too (toggleable via `config.json`'s
`checks` object — a repo whose tests don't sit in a predictable place relative to the
code has nothing to gain from it).

This does **not** re-derive coverage percentages or re-implement test running — it
delegates the run to `run-tests` and keeps only the "did the tests keep up" question for
itself.

**Slice *shape* is not checked here.** Whether a use-case package carries its Test-API
and fakes, and whether a spec reaches past the Test-API into domain/handler/mapper
internals, is the job of the `slice-shape-check` skill — it is diff-scoped, fully
deterministic, and matches this repo's actual package layout. Don't duplicate it here.

Everything repo-specific — which checks are active, and the map from a production unit to
where its tests live — lives in `config.json`. Nothing repo-specific belongs in this file.

## Process

1. **Read `config.json`'s `checks` object.** `coverage_gap` defaults to `true` if the key
   is absent. A disabled check gets one report row saying `disabled via config` — never
   silently folded into a `0`, so a reader can't mistake "not checked" for "checked and
   clean".

2. **Run the suite.** Use this repo's canonical test runner, unmodified:
   ```powershell
   uv run .claude/skills/run-tests/scripts/run-tests.py
   ```
   Exit 0 → suite green. Exit ≠ 0 → paste the failing test names/errors verbatim (same
   rule `run-tests` itself follows) — do not summarize them away.

3. **If `checks.coverage_gap` is enabled**, run:
   ```powershell
   uv run .claude/skills/qa-check/scripts/coverage_gap.py [base-ref]
   ```

   The script reads `coverage_rules` from `config.json` — an ordered list pairing a glob
   matching a production unit with a template naming where that unit's tests live
   (`{0}`, `{1}`, … are the glob's wildcard captures, in order). Rules are matched against
   the changed **path itself**, in order, first match winning; since they run
   specific-before-general, that also yields the most specific unit containing the path, so
   a change inside a slice is judged against the slice's own tests rather than its parent
   package.

   Deletions and renames count. A deleted production file is a change its tests must keep
   up with, and a renamed unit is reported from both sides — the old path as a `gap` (its
   tests just went stale) and the new one as `no-test-location` (it may have none yet).
   This is why units are resolved from the path rather than from what currently sits on
   disk: a removed unit is gone from the checkout and could never be enumerated there.

   Exit 2 with `Verdict: CONFIG ERROR` means `coverage_rules` is missing — per
   `_shared/validator-contract.md`, stop and report that, don't treat it as a pass.

   Each changed unit gets one row:

   - `covered` — something under its test location changed too.
   - `gap` — the test location exists on disk but didn't change.
   - `no-test-location` — the mapped test location doesn't exist. Not automatically a
     finding, but **do** report it: it usually means `coverage_rules` has drifted from the
     layout, not that tests are genuinely unnecessary.

   A changed path under `src/` that no rule claims is listed as `unmapped`. That is a
   config-drift signal, not a clean result — surface it rather than ignoring it.

   Judge `gap` rows, don't rubber-stamp them: a pure rename, a comment-only change, or a
   change already fully covered by an existing test can legitimately need no new test.
   Read the diff for each `gap` row before counting it as a finding; drop it (and say why)
   if it's a genuine no-test-needed change.

## Report format

**Verdict: PASS** or **Verdict: FAIL** (FAIL if the suite is red or any enabled `gap` row
survives judgement), then:

| Check | Result |
| ----- | ------ |
| Test suite | green / red (`N` gesamt, `M` fehlgeschlagen) |
| Coverage gaps | `<unit>` — gap / dismissed (reason) / no-test-location / unmapped / disabled via config |

For a red suite, the verbatim failing test names underneath. End with:

```
Findings: <n>
```

`<n>` = failing tests (0 if green) + surviving coverage-gap rows (0 if disabled). A
disabled check contributes `0`, but its row says `disabled via config`, not a bare `0`, so
it's never mistaken for "checked, clean".
