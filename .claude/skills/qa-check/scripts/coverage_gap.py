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
that enumerates production units with a template naming where that unit's
tests live:

    "coverage_rules": [
      {"unit_glob": "src/contexts/*/application/*",
       "test_template": "src/contexts/{0}/specs/{1}"},
      {"unit_glob": "src/*", "test_template": "tests/{0}"}
    ]

`{0}`, `{1}`, ... are the wildcard captures of `unit_glob`, in order. Rules are
matched in order and the first rule to claim a path wins, so specific rules go
before general ones. A changed path under `src/` that no rule claims is
reported as `unmapped` rather than dropped -- an unmappable path means the
config has drifted from the layout, and silence there would read as "clean".

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
from skill_git import GitError, changed_paths, resolve_merge_base

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / "config.json"
REQUIRED_KEYS = ("coverage_rules",)
SRC_PREFIX = "src/"


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


def captures(unit_glob: str, path: str) -> tuple[str, ...] | None:
    """Pull the wildcard captures out of `path` for `unit_glob`.

    Segment-wise so a `*` never eats a `/`: each glob segment becomes a regex
    where `*` is a capturing `(.*)`, everything else is literal. Returns None
    when the path does not match the glob at all.
    """
    glob_parts, path_parts = unit_glob.split("/"), path.split("/")
    if len(glob_parts) != len(path_parts):
        return None
    found: list[str] = []
    for glob_part, path_part in zip(glob_parts, path_parts):
        pattern = "".join("(.*)" if ch == "*" else re.escape(ch) for ch in glob_part)
        match = re.fullmatch(pattern, path_part)
        if match is None:
            return None
        found.extend(match.groups())
    return tuple(found)


def discover_units(rules: list[dict], exclude: frozenset[str]) -> tuple[Unit, ...]:
    """Enumerate every production unit on disk, first matching rule winning."""
    claimed: set[str] = set()
    units: list[Unit] = []
    for rule in rules:
        unit_glob, template = rule["unit_glob"], rule["test_template"]
        for found in sorted(Path().glob(unit_glob)):
            path = found.as_posix()
            if path in claimed or found.name in exclude:
                continue
            groups = captures(unit_glob, path)
            if groups is None:
                continue
            claimed.add(path)
            units.append(Unit(path, template.format(*groups)))
    return tuple(units)


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

    # Two lists, deliberately: production units are looked for under src/, but a
    # test location may live anywhere (this repo has both src/.../specs/ and a
    # top-level tests/), so the "did tests change too" question needs the
    # unfiltered diff.
    all_changed = changed_paths(merge_base)
    units = discover_units(rules, exclude)

    # A test location can itself sit under src/ (this repo keeps slice specs at
    # src/contexts/<ctx>/specs/<use_case>/). Changing a spec is not a production
    # change, so those paths are dropped before anything is attributed -- without
    # this, a spec-only commit would report its own context as an uncovered gap.
    test_locations = {u.test_location for u in units}
    changed = tuple(
        p
        for p in all_changed
        if p.startswith(SRC_PREFIX) and not any(is_under(p, loc) for loc in test_locations)
    )

    # Units nest (a slice package sits inside its context, which sits inside
    # src/contexts). A changed path counts toward the *most specific* unit that
    # contains it, so a slice change is judged against the slice's own specs and
    # never also against its parent -- and a pure container, whose every change
    # belongs to some child, produces no row at all.
    owner: dict[str, list[str]] = {u.path: [] for u in units}
    mapped: set[str] = set()
    for path in changed:
        containing = [u.path for u in units if is_under(path, u.path)]
        if not containing:
            continue
        owner[max(containing, key=len)].append(path)
        mapped.add(path)

    rows: list[UnitRow] = []
    for unit in units:
        if not owner[unit.path]:
            continue
        if not Path(unit.test_location).exists():
            status = CoverageStatus.NO_TEST_LOCATION
        elif any(is_under(p, unit.test_location) for p in all_changed):
            status = CoverageStatus.COVERED
        else:
            status = CoverageStatus.GAP
        rows.append(UnitRow(unit.path, unit.test_location, status))

    unmapped = sorted(set(changed) - mapped)

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
