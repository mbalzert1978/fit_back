#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Flag changed production units whose configured test location did not change too.

This is a heuristic, not a coverage percentage: it only proves "something in
the matching test location changed too", not that the right behavior is
tested. Judge the actual test content yourself; this script just finds
candidates.

The production-unit -> test-location mapping is **not** hardcoded. A repo
declares it as an ordered list of rules in config.json, each pairing a glob
matching a production unit with a template naming where that unit's tests live:

    "coverage_rules": [
      {"unit_glob": "src/contexts/*/application/*",
       "test_template": "src/contexts/{0}/specs/{1}"},
      {"unit_glob": "src/*", "test_template": "tests/{0}"}
    ]

`{0}`, `{1}`, ... are the wildcard captures of `unit_glob`, in order.

A changed path is attributed by matching the rules against the **path itself**,
in order, first match winning -- not by enumerating what currently sits on disk.
That distinction is the whole point: a deleted or renamed unit is gone from the
checkout, so disk enumeration could never map it, and its now-stale tests would
go unnoticed. Since rules are ordered specific-before-general, the first rule to
match a path prefix also yields the most specific unit containing it, so a slice
change is judged against the slice's own tests rather than its parent package.

Deletions are deliberately part of the diff here (unlike `skill_git.changed_paths`,
which excludes them for callers that read file contents): deleting production code
is a change its tests must keep up with.

A changed path under `src/` that no rule claims is reported as `unmapped` rather
than dropped -- an unmappable path means the config has drifted from the layout,
and silence there would read as "clean".

Usage:
  coverage_gap.py [base-ref] [--json]
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from skill_config import load_config
from skill_git import GitError, git, resolve_merge_base

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / "config.json"
REQUIRED_KEYS = ("coverage_rules",)
SRC_PREFIX = "src/"
PLACEHOLDER = re.compile(r"\{\d+\}")


class CoverageStatus(Enum):
    """The exclusive, closed set of coverage verdicts a changed unit can carry."""

    COVERED = "covered"
    GAP = "gap"
    NO_TEST_LOCATION = "no-test-location"


@dataclass(frozen=True)
class Unit:
    """A production unit and the test location its rule maps it to."""

    path: str
    test_location: str


@dataclass(frozen=True)
class UnitRow:
    unit: str
    test_location: str
    status: CoverageStatus


def changed_paths_including_deletions(merge_base: str) -> tuple[str, ...]:
    """Every path the diff touches, deletions and both sides of a rename included.

    Two departures from `skill_git.changed_paths`, both because this caller maps
    path strings instead of reading file contents:

    - it drops `--diff-filter=d`, so deletions count -- deleting production code is
      a change its tests must keep up with;
    - it passes `--no-renames`, because rename detection collapses a move into the
      new path alone. Here both sides matter: the old path is the unit whose tests
      just went stale, the new one is the unit that may have none yet.
    """
    names = git("diff", "--name-only", "--no-renames", merge_base)
    return tuple(n for n in names.stdout.splitlines() if n.strip())


def match_prefix(glob: str, path: str) -> tuple[str, tuple[str, ...]] | None:
    """Match `glob` against the leading segments of `path`.

    Segment-wise so a `*` never eats a `/`: each glob segment becomes a regex
    where `*` is a capturing `(.*)`, everything else literal. Returns the matched
    prefix and the captures, or None when the leading segments don't match.
    """
    glob_parts, path_parts = glob.split("/"), path.split("/")
    if len(path_parts) < len(glob_parts):
        return None
    head = path_parts[: len(glob_parts)]
    found: list[str] = []
    for glob_part, path_part in zip(glob_parts, head):
        pattern = "".join("(.*)" if ch == "*" else re.escape(ch) for ch in glob_part)
        match = re.fullmatch(pattern, path_part)
        if match is None:
            return None
        found.extend(match.groups())
    return "/".join(head), tuple(found)


def resolve_unit(rules: list[dict], path: str, exclude: frozenset[str]) -> Unit | None:
    """Find the unit owning `path` by applying the rules in order."""
    for rule in rules:
        matched = match_prefix(rule["unit_glob"], path)
        if matched is None:
            continue
        unit_path, groups = matched
        # A directory named here isn't a unit of its own (`shared`, `__pycache__`);
        # fall through so a more general rule can claim the path instead.
        if unit_path.rsplit("/", 1)[-1] in exclude:
            continue
        return Unit(unit_path, rule["test_template"].format(*groups))
    return None


def test_area_globs(rules: list[dict]) -> tuple[str, ...]:
    """The path globs that are test territory, derived from the rules themselves.

    A test location can sit under `src/` (slice specs do). Substituting `*` for each
    template placeholder turns `src/contexts/{0}/specs/{1}` into
    `src/contexts/*/specs/*` -- so test areas need no config of their own, and can't
    drift from the mapping they come from.
    """
    return tuple({PLACEHOLDER.sub("*", rule["test_template"]) for rule in rules})


def is_under(path: str, root: str) -> bool:
    """Does `path` name `root` itself or something inside it?"""
    return path == root or path.startswith(root + "/")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Flag changed production units with no accompanying test change."
    )
    ap.add_argument("base", nargs="?", help="base ref to diff against (default: auto-resolved)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    config = load_config(CONFIG)
    missing = [key for key in REQUIRED_KEYS if not config.get(key)]
    if missing:
        print(
            f"Verdict: CONFIG ERROR\nmissing key(s) in {CONFIG}: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    rules = config["coverage_rules"]
    exclude = frozenset(config.get("coverage_exclude_names", ()))

    match resolve_merge_base(args.base):
        case GitError() as err:
            print(f"error: {err.message}", file=sys.stderr)
            return 1
        case merge_base:
            pass

    all_changed = changed_paths_including_deletions(merge_base)
    test_areas = test_area_globs(rules)

    # Changing a test is not a production change. Slice specs live under src/, so
    # this can't be a plain prefix filter -- without it, a spec-only commit would
    # report its own context as an uncovered gap.
    production = tuple(
        p
        for p in all_changed
        if p.startswith(SRC_PREFIX)
        and not any(match_prefix(area, p) is not None for area in test_areas)
    )

    units: dict[str, Unit] = {}
    unmapped: list[str] = []
    for path in production:
        unit = resolve_unit(rules, path, exclude)
        if unit is None:
            unmapped.append(path)
            continue
        units[unit.path] = unit

    rows: list[UnitRow] = []
    for unit in units.values():
        if not Path(unit.test_location).exists():
            status = CoverageStatus.NO_TEST_LOCATION
        elif any(is_under(p, unit.test_location) for p in all_changed):
            status = CoverageStatus.COVERED
        else:
            status = CoverageStatus.GAP
        rows.append(UnitRow(unit.path, unit.test_location, status))

    rows.sort(key=lambda r: r.unit)
    unmapped.sort()

    if args.json:
        print(
            json.dumps(
                {
                    "units": [{**asdict(r), "status": r.status.value} for r in rows],
                    "unmapped": unmapped,
                },
                indent=2,
            )
        )
        return 0

    if not rows and not unmapped:
        print("(no production units changed)")
    for row in rows:
        print(f"{row.unit:<55} {row.status.value:<18} -> {row.test_location}")
    for path in unmapped:
        print(f"{path:<55} unmapped           (no coverage_rules entry claims it)")
    gaps = [r for r in rows if r.status is CoverageStatus.GAP]
    print(f"\ngaps: {len(gaps)}  unmapped: {len(unmapped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
