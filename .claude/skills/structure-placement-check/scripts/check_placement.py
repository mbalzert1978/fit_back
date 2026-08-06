#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Flag changed test files that live outside this repo's configured test roots.

Purely mechanical file-*path* check — no code content is read. A test file
(matching a configured naming pattern) must live under one of the configured
test-root prefixes (co-located under its own module, e.g. `src/shared_kernel/
tests/`, or per-use-case under a context, e.g. `src/contexts/diary/tests/
register_meal/`); anything else — a stray top-level `tests/` mirror tree, a
test file dropped straight into a domain/application/infrastructure folder —
is a finding. Both patterns come from config.json, so the check stays
portable across repos with a different layout.

`exempt_file_names` carves out files that merely *look* like test files but are
shipped parts of a slice — `test_api.py` is the public Test-API of a use case
and belongs inside `application/<use_case>/`, not under a test root.

The report ALWAYS states how many changed files were actually inspected — a run
that had nothing to check must not read like a run that verified everything.

Usage:
  check_placement.py [base-ref] [--json]
"""

import argparse
import fnmatch
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from skill_config import load_config
from skill_git import GitError, changed_paths, resolve_merge_base

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / "config.json"
REQUIRED_KEYS = ("test_file_patterns", "test_root_prefixes")


def is_test_file(path: str, patterns: list[str], exempt: list[str]) -> bool:
    name = path.rsplit("/", 1)[-1]
    if name in exempt:
        return False
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def matches_any_prefix(path: str, prefixes: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, prefix.rstrip("/") + "/*") for prefix in prefixes)


def check(paths: tuple[str, ...], config: dict) -> tuple[list[str], int]:
    """Return the findings plus how many changed files were actually judged."""
    test_patterns = config["test_file_patterns"]
    test_prefixes = config["test_root_prefixes"]
    exempt = config.get("exempt_file_names", [])
    inspected = [p for p in paths if is_test_file(p, test_patterns, exempt)]
    findings = [
        f"{path}: test file is outside every configured test root ({', '.join(test_prefixes)})"
        for path in inspected
        if not matches_any_prefix(path, test_prefixes)
    ]
    return findings, len(inspected)


def main() -> int:
    ap = argparse.ArgumentParser(description="Flag changed test files violating the configured placement rule.")
    ap.add_argument("base", nargs="?", help="base ref to diff against (default: auto-detected)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    config = load_config(CONFIG)
    missing = [k for k in REQUIRED_KEYS if not config.get(k)]
    if missing:
        print("Verdict: CONFIG ERROR")
        print(
            f"Missing/empty required config.json key(s): {', '.join(missing)} "
            f"(set them in .claude/skills/structure-placement-check/config.json)"
        )
        return 2

    match resolve_merge_base(args.base):
        case GitError(message):
            print(f"error: {message}", file=sys.stderr)
            return 1
        case merge_base:
            pass

    paths = changed_paths(merge_base)
    findings, inspected = check(paths, config)

    if args.json:
        print(json.dumps({"findings": findings, "inspected": inspected}, indent=2))
        return 0

    print("Verdict: BLOCK" if findings else "Verdict: APPROVE")
    print(f"Scope: {len(paths)} changed file(s), {inspected} test file(s) inspected")
    for f in findings:
        print(f"- {f}")
    print(f"Findings: {len(findings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
