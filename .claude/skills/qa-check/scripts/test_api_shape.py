#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Enumerate candidate test-facade files for the Fowler Test-API-shape check.

This script does NOT judge the shape (fluent arrange, hidden internals, correct
dependency direction) -- that is a semantic property, not a syntactic one, and
regex-matching a specific language's syntax (an earlier version of this script
did that for C#) is both language-locked and fragile (word-boundary bugs on
compound identifiers, false positives on legitimate naming variation). The
judgment is instead made by whichever agent runs the qa-check skill, against
the checklist in its SKILL.md -- the same split architecture-adr-check already
uses (script lists candidates mechanically, agent judges compliance).

This script only answers the mechanical, language-agnostic question: for each
in-scope feature project, does at least one file exist matching the configured
`test_facade_glob`?

Usage:
  test_api_shape.py [--json]
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from skill_config import load_config

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / "config.json"
SRC = Path("src")


@dataclass(frozen=True)
class Candidate:
    feature: str
    files: list[str]


def main() -> int:
    ap = argparse.ArgumentParser(description="List test-facade candidates per feature project.")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    as_json = args.json
    cfg = load_config(CONFIG)
    prefix = cfg.get("feature_project_prefix", "")
    specs_suffix = cfg.get("specs_suffix", ".Specs")
    glob = cfg.get("test_facade_glob", "Application/TestApis/*TestApi.cs")

    feature_dirs = sorted(
        p for p in SRC.iterdir()
        if p.is_dir() and p.name.startswith(prefix) and not p.name.endswith(specs_suffix)
    )

    if not feature_dirs:
        print(f"error: no feature projects found under {SRC} matching prefix {prefix!r}", file=sys.stderr)
        return 1

    rows = [Candidate(d.name, sorted(str(p) for p in d.glob(glob))) for d in feature_dirs]

    if as_json:
        print(json.dumps({"glob": glob, "features": [asdict(r) for r in rows]}, indent=2))
        return 0

    missing = [r for r in rows if not r.files]
    for r in rows:
        status = ", ".join(r.files) if r.files else "MISSING (no file matches the configured glob)"
        print(f"{r.feature:<55} {status}")
    print(f"\nglob: {glob}")
    print(f"missing: {len(missing)}")
    print("(features with a match still need agent judgment against the Fowler checklist in SKILL.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
