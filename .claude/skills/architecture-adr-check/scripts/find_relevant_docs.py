#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Mechanical grounding for architecture-adr-check: list ADRs, list/rank issues.

Does NOT decide relevance or compliance — that's the judgement pass in the
skill. This only extracts what the repo records so the agent isn't
hand-transcribing titles and states, and ranks issues by a crude keyword
overlap with the changed paths as a starting point, not a filter.

ADRs are files; issues are GitHub sub-issues of the wayfinder map named by
`issue_map` in config.json, fetched with `gh`. The three status values the
skill filters on are derived, not stored: closed issue -> `closed`, open with
open blockers -> `blocked`, open without -> `open`.

Usage:
  find_relevant_docs.py adrs [--json]
  find_relevant_docs.py issues [--status open] [--match PATH ...] [--json]
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from skill_config import load_config

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / "config.json"

STOPWORDS = {"und", "der", "die", "das", "fuer", "mit", "von", "auf", "ein", "eine", "the", "and", "for", "with"}


def configured_sources() -> tuple[Path | None, int | None]:
    cfg = load_config(CONFIG)
    adr_dir = cfg.get("adr_dir")
    issue_map = cfg.get("issue_map")
    return (Path(adr_dir) if adr_dir else None, int(issue_map) if issue_map else None)


def tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-zA-Z0-9]+", text.lower()) if len(t) > 2 and t not in STOPWORDS}


@dataclass(frozen=True)
class Adr:
    id: str
    file: str
    title: str


def list_adrs(adr_dir: Path) -> list[Adr]:
    out = []
    for f in sorted(adr_dir.glob("*.md")):
        m = re.match(r"(\d+)-", f.name)
        adr_id = m.group(1) if m else f.stem
        first_line = next((l.strip("# ").strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()), f.stem)
        out.append(Adr(adr_id, str(f), first_line))
    return out


@dataclass(frozen=True)
class Issue:
    id: str
    url: str
    title: str
    status: str
    score: int


def fetch_sub_issues(issue_map: int) -> list[dict]:
    """Every child of the map, across pages.

    Raises on a gh failure — an empty list would read as "no issue matches" and
    produce a false PASS. `--paginate` is required: without it GitHub returns
    only the first 30 children and gives no sign that more exist.
    """
    proc = subprocess.run(
        ["gh", "api", "--paginate", f"repos/{{owner}}/{{repo}}/issues/{issue_map}/sub_issues"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh api failed for map #{issue_map}: {proc.stderr.strip()}")
    # --paginate concatenates one JSON array per page.
    decoder, pos, out = json.JSONDecoder(), 0, []
    payload = proc.stdout.strip()
    while pos < len(payload):
        page, pos = decoder.raw_decode(payload, pos)
        out.extend(page)
        while pos < len(payload) and payload[pos].isspace():
            pos += 1
    return out


def derive_status(raw: dict) -> str:
    if raw.get("state") == "closed":
        return "closed"
    summary = raw.get("issue_dependencies_summary") or {}
    return "blocked" if summary.get("blocked_by", 0) > 0 else "open"


def list_issues(issue_map: int, status: str | None, match_tokens: set[str]) -> list[Issue]:
    out = []
    for raw in fetch_sub_issues(issue_map):
        issue_status = derive_status(raw)
        if status and issue_status != status:
            continue
        title = raw.get("title", "")
        # Substring overlap, not exact match: German compounds ("BatchTausch")
        # won't split the same way a path segment ("Batch") does.
        title_tokens = tokens(title)
        score = sum(
            1 for t in title_tokens for m in match_tokens if t in m or m in t
        ) if match_tokens else 0
        out.append(Issue(str(raw.get("number", "")), raw.get("html_url", ""), title, issue_status, score))
    out.sort(key=lambda i: i.score, reverse=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    adrs_p = sub.add_parser("adrs")
    adrs_p.add_argument("--json", action="store_true")

    issues_p = sub.add_parser("issues")
    issues_p.add_argument("--status")
    issues_p.add_argument("--match", nargs="*", default=[])
    issues_p.add_argument("--json", action="store_true")

    args = ap.parse_args()

    adr_dir, issue_map = configured_sources()

    if adr_dir is None or issue_map is None:
        missing = [n for n, v in (("adr_dir", adr_dir), ("issue_map", issue_map)) if v is None]
        print(f"error: {', '.join(missing)} not configured in config.json", file=sys.stderr)
        return 1

    if args.cmd == "adrs":
        rows = list_adrs(adr_dir)
        if args.json:
            print(json.dumps([asdict(r) for r in rows], indent=2))
        else:
            for r in rows:
                print(f"{r.id}  {r.title}  ({r.file})")
        return 0

    match_tokens: set[str] = set()
    for p in args.match:
        match_tokens |= tokens(p)
    try:
        rows = list_issues(issue_map, args.status, match_tokens)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps([asdict(r) for r in rows], indent=2))
    else:
        for r in rows:
            print(f"#{r.id}  score={r.score}  status={r.status}  {r.title}  ({r.url})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
