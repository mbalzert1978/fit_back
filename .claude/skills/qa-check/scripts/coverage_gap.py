#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Flag changed src/ projects with no accompanying change in their co-located
*.Specs project (ADR-0006: tests are co-located per feature under specs).

This is a heuristic, not a coverage percentage: it only proves "something in
the sibling Specs project changed too", not that the right behavior is tested.
Judge the actual test content yourself; this script just finds candidates.

Usage:
  coverage_gap.py [base-ref] [--json]

Prints one row per changed top-level src/ project: covered (a sibling
*.Specs project also changed), gap (production changed, its *.Specs sibling
exists on disk but did not change), or no-specs-sibling (no *.Specs project
exists for this one — not a gap, there is nothing to require).
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from skill_config import load_config
from skill_git import GitError, changed_paths, resolve_merge_base

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / "config.json"


class CoverageStatus(Enum):
    """The exclusive, closed set of coverage verdicts a changed project can carry."""

    COVERED = "covered"
    GAP = "gap"
    NO_SPECS_SIBLING = "no-specs-sibling"


@dataclass(frozen=True)
class ProjectRow:
    project: str
    specs_dir: str
    status: CoverageStatus


def changed_src_files(base: str | None) -> tuple[str, ...] | GitError:
    match resolve_merge_base(base):
        case GitError() as err:
            return err
        case merge_base:
            pass
    return tuple(n for n in changed_paths(merge_base) if n.strip().startswith("src/"))


def top_level_project(path: str) -> str | None:
    parts = Path(path).parts
    return parts[1] if len(parts) > 1 else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Flag changed src/ projects with no accompanying Specs change.")
    ap.add_argument("base", nargs="?", help="base ref to diff against (default: auto-resolved)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    as_json = args.json
    base = args.base
    suffix = load_config(CONFIG).get("specs_suffix", ".Specs")

    files = changed_src_files(base)
    if isinstance(files, GitError):
        print(f"error: {files.message}", file=sys.stderr)
        return 1

    touched = {p for f in files if (p := top_level_project(f))}
    src_root = Path("src")

    rows: list[ProjectRow] = []
    for project in sorted(touched):
        if project.endswith(suffix):
            continue  # this IS a specs project change, not something requiring one
        specs_dir = project + suffix
        specs_exists_on_disk = (src_root / specs_dir).is_dir()
        specs_changed = specs_dir in touched
        if not specs_exists_on_disk:
            status = CoverageStatus.NO_SPECS_SIBLING
        elif specs_changed:
            status = CoverageStatus.COVERED
        else:
            status = CoverageStatus.GAP
        rows.append(ProjectRow(project, specs_dir, status))

    if as_json:
        files_out = [{**asdict(r), "status": r.status.value} for r in rows]
        print(json.dumps(files_out, indent=2))
        return 0

    gaps = [r for r in rows if r.status is CoverageStatus.GAP]
    if not rows:
        print("(no src/ projects changed)")
    for r in rows:
        print(f"{r.project:<55} {r.status.value}")
    print(f"\ngaps: {len(gaps)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
