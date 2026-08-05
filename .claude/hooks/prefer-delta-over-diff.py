#!/usr/bin/env python3
# PreToolUse(Bash) guard: blocks bare diff calls, enforces delta.
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input, bash_command

data = load_hook_input()

BSP = r"""
# delta Quick Reference (LLM-optimized)

## What delta is
Syntax-highlighting pager for diff output. Configure once in .gitconfig;
git pipes through it automatically. Also callable directly.

## Primary setup (.gitconfig)
[core]
    pager = delta

[interactive]
    diffFilter = delta --color-only   # required for git add -p

[delta]
    navigate = true
    side-by-side = true
    line-numbers = true
    syntax-theme = TwoDark

## Direct invocation
delta FILE1 FILE2            # diff two files with delta rendering
diff -u old new | delta      # pipe any unified diff through delta

## Essential flags
--side-by-side / -s         two-column view
--line-numbers / -n         show line numbers
--navigate                  n/N to jump between diff sections
--light / --dark            background theme selection
--syntax-theme THEME        set highlighting theme
--color-only                ANSI color only (required for git add -p)
--paging=auto|always|never  pager control

## Common patterns
delta old.cs new.cs                          # two-file diff
diff -u before.txt after.txt | delta         # pipe unified diff
git diff --no-index dir1 dir2                # directory diff (delta pager applies)
git diff | delta --paging=never              # no pager (scripts/CI)
delta --show-syntax-themes                   # preview available themes

## Replacing plain diff
diff file1 file2        ->  delta file1 file2
diff -u file1 file2     ->  delta file1 file2
diff -r dir1 dir2       ->  git diff --no-index dir1 dir2

## Notes
- delta NEVER modifies files — display only
- git commands use delta automatically once pager is configured
- --color-only REQUIRED in [interactive] diffFilter or git add -p breaks
"""

command = bash_command(data)

# Block bare `diff` command used for file comparison.
# Allow: `git diff` (delta pager already applies), `--no-index` (already uses delta).
# Block: `diff FILE1 FILE2`, `diff -u …`, `diff -r …`
is_bare_diff = re.search(r'(?:^|[;&|`\s])\s*diff\b', command)
is_git_diff  = re.search(r'\bgit\s+diff\b', command)

if is_bare_diff and not is_git_diff:
    sys.stderr.write(
        "Blockiert: diff ist verboten. Nutze stattdessen delta — "
        "Syntax-Highlighting, Side-by-Side-Ansicht, Git-Integration.\n"
        "Für Datei-Vergleiche: delta file1 file2\n"
        "Für Directory-Diffs: git diff --no-index dir1 dir2\n"
        f"Beispiel:{BSP}"
    )
    sys.exit(2)

sys.exit(0)
