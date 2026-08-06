#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check the mechanically-verifiable half of this repo's feature-slice form.

Three path/import-level checks, all deterministic — no code is judged, only
structure:

  1. every use-case package carries a Test-API (`test_api.py`)
  2. every use-case package carries in-memory fakes (`fakes/`)
  3. no spec reaches past the Test-API — a spec may import the Test-API and the
     public request/response DTOs, never the domain, the handler, the mappers,
     the fakes, or infrastructure

Scope is the diff by default (only use cases touched by the current branch), so
pre-existing debt doesn't re-flag on every PR; `--all` sweeps the whole repo.

The report ALWAYS states how many use cases and specs were actually inspected —
a run that found nothing to check must not read like a run that verified
everything.

Usage:
  check_slice_shape.py [base-ref] [--all] [--json]
"""

import argparse
import ast
import fnmatch
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from skill_config import load_config
from skill_git import GitError, changed_paths, git, resolve_merge_base

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / "config.json"
REQUIRED_KEYS = (
    "use_case_glob",
    "required_files",
    "required_dirs",
    "spec_glob",
    "spec_file_patterns",
    "spec_forbidden_import_fragments",
)


def repo_root() -> Path:
    return Path(git("rev-parse", "--show-toplevel").stdout.strip())


def use_case_dirs(root: Path, config: dict) -> list[Path]:
    excluded = set(config.get("use_case_exclude_names", []))
    return sorted(
        d for d in root.glob(config["use_case_glob"]) if d.is_dir() and d.name not in excluded
    )


def spec_files(root: Path, config: dict) -> list[Path]:
    """Use-case spec files only.

    `spec_exclude_dir_names` carves out the sibling test folders that are NOT
    use-case specs and legitimately reach into the domain: domain unit tests
    (per-aggregate/VO/union, BACKEND.md section 9) and cross-context contract
    tests (docs/milestones/02-test-pyramide.md). Judging those by the
    "never import .domain" rule would forbid the very thing they exist to test.
    """
    patterns = config["spec_file_patterns"]
    excluded = set(config.get("spec_exclude_dir_names", []))
    return sorted(
        f
        for d in root.glob(config["spec_glob"])
        if d.is_dir() and d.name not in excluded
        for f in d.rglob("*.py")
        if any(fnmatch.fnmatch(f.name, p) for p in patterns)
    )


def imported_modules(path: Path) -> list[str]:
    """Every module string a file imports, via `import x` and `from x import y`."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []
    out: list[str] = []
    for node in ast.walk(tree):
        match node:
            case ast.Import(names=names):
                out += [a.name for a in names]
            case ast.ImportFrom(module=module) if module:
                out.append(module)
    return out


def check_use_case(directory: Path, root: Path, config: dict) -> list[str]:
    rel = directory.relative_to(root).as_posix()
    missing_files = [f for f in config["required_files"] if not (directory / f).is_file()]
    missing_dirs = [d for d in config["required_dirs"] if not (directory / d).is_dir()]
    return [
        f"{rel}/: use case is missing {name}"
        for name in [*missing_files, *(f"{d}/" for d in missing_dirs)]
    ]


def check_spec(path: Path, root: Path, config: dict) -> list[str]:
    rel = path.relative_to(root).as_posix()
    forbidden = config["spec_forbidden_import_fragments"]
    return [
        f"{rel}: spec imports `{module}` - reaches past the Test-API (forbidden fragment `{frag}`)"
        for module in imported_modules(path)
        for frag in forbidden
        if frag in module
    ]


def touched(directory: Path, root: Path, changed: set[str]) -> bool:
    prefix = directory.relative_to(root).as_posix() + "/"
    return any(c.startswith(prefix) for c in changed)


def main() -> int:
    ap = argparse.ArgumentParser(description="Check the feature-slice form (structure only).")
    ap.add_argument("base", nargs="?", help="base ref to diff against (default: auto-detected)")
    ap.add_argument("--all", action="store_true", help="sweep the whole repo, not just the diff")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    config = load_config(CONFIG)
    missing = [k for k in REQUIRED_KEYS if not config.get(k)]
    if missing:
        print("Verdict: CONFIG ERROR")
        print(
            f"Missing/empty required config.json key(s): {', '.join(missing)} "
            f"(set them in .claude/skills/slice-shape-check/config.json)"
        )
        return 2

    match resolve_merge_base(args.base):
        case GitError(message):
            print(f"error: {message}", file=sys.stderr)
            return 1
        case merge_base:
            pass

    root = repo_root()
    changed = set(changed_paths(merge_base))
    cases = use_case_dirs(root, config)
    specs = spec_files(root, config)
    if not args.all:
        cases = [c for c in cases if touched(c, root, changed)]
        specs = [s for s in specs if s.relative_to(root).as_posix() in changed]

    findings = [f for c in cases for f in check_use_case(c, root, config)]
    findings += [f for s in specs for f in check_spec(s, root, config)]

    scope = f"{len(cases)} use case(s), {len(specs)} spec file(s) inspected"
    if args.json:
        print(json.dumps({"scope": scope, "findings": findings}, indent=2))
        return 0

    print("Verdict: BLOCK" if findings else "Verdict: APPROVE")
    print(f"Scope: {scope}")
    for f in findings:
        print(f"- {f}")
    print(f"Findings: {len(findings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
