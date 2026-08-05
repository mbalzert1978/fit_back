#!/usr/bin/env python3
# PreToolUse(Bash) guard: blocks cat/head/tail calls, enforces bat.
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input, bash_command

data = load_hook_input()

BSP = r"""
# bat Quick Reference (LLM-optimized)

## Invocation forms
bat FILE                # print file with syntax highlighting + line numbers
bat FILE1 FILE2         # concatenate multiple files
bat -                   # read from stdin
bat FILE -r 10:30       # print only lines 10–30
bat FILE -H 42          # print file, highlight line 42

## Essential flags
-n / --number               show line numbers only (no grid/header)
-p / --plain                plain output: no line numbers, no grid, no header
-A / --show-all             show non-printable chars (tabs, spaces, newlines)
-d / --diff                 show only changed lines (git diff mode)
-S / --chop-long-lines      truncate lines at screen width
-s / --squeeze-blank        collapse consecutive blank lines
-u / --unbuffered           unbuffered stdin (streaming use cases)
-E / --quiet-empty          no output when input is empty

## Line selection (replaces head / tail / sed -n)
-r N:M / --line-range N:M   lines N through M (1-based, inclusive)
-r :M                       start to line M          (replaces head -n M)
-r N:                       line N to end of file
-r -N:                      last N lines             (replaces tail -n N)

## Language / syntax
-l LANG / --language LANG       force syntax (e.g. -l json, -l cs, -l yaml)
-m 'GLOB:LANG' / --map-syntax   map files by glob (e.g. '*.config:XML')
-L / --list-languages           list all supported languages

## Output control
--color=auto|never|always       color (default: auto)
--paging=auto|never|always      pager control (default: auto)
-P                              disable pager (shorthand for --paging=never)
--style COMPONENTS              plain, full, auto, changes, header, grid, numbers, snip
--wrap=auto|never|character|word  text wrap mode (default: auto)

## Common patterns
bat -pp FILE                        # plain cat (no decorations, no pager)
bat FILE -r :20                     # first 20 lines  (replaces head -n 20)
bat FILE -r -20:                    # last 20 lines   (replaces tail -n 20)
bat FILE -r 50:100                  # lines 50–100
bat -l json response.log            # force JSON syntax
bat --diff FILE                     # show only git-changed lines
some-command | bat -l log --paging=never  # colorized pipe output
bat --paging=never FILE             # no pager (safe in scripts)
bat -A FILE                         # debug non-printable / encoding issues
bat -s FILE                         # squeeze blank lines

## Notes
- bat NEVER modifies files (read-only, like cat)
- tail -f has no bat equivalent — use tail -f directly for log following
- In non-TTY / pipe contexts decorations are off by default (--decorations=auto)
"""

command = bash_command(data)

# Block cat unless it is a heredoc (cat <<EOF / cat << 'EOF')
cat_match = re.search(r'(?:^|[;&|`\s])\s*cat(?:\s|$)', command)
heredoc   = re.search(r'\bcat\s*<<', command)

# Block head and tail (lowercase only; git's HEAD is uppercase and won't match)
head_match = re.search(r'(?:^|[;&|`\s])\s*head(?:\s|$)', command)
tail_match = re.search(r'(?:^|[;&|`\s])\s*tail\s+(?!-f)', command)  # allow tail -f (log following)

blocked = []
if cat_match and not heredoc:
    blocked.append("cat")
if head_match:
    blocked.append("head")
if tail_match:
    blocked.append("tail (non -f)")

if blocked:
    tools = " / ".join(blocked)
    sys.stderr.write(
        f"Blockiert: {tools} ist verboten. Nutze stattdessen bat — "
        "Syntax-Highlighting, Zeilennummern, Git-Diff-Ansicht, Zeilen-Ranges.\n"
        f"Ausnahme: tail -f bleibt erlaubt (Log-Following).\n"
        "WICHTIG: Kein Fallback auf Grep- oder Read-Tools als Ersatz. "
        "Den Bash-Befehl mit bat korrigieren (z.B. `| head -N` → `| bat -r :N --paging=never`).\n"
        f"Beispiel:{BSP}"
    )
    sys.exit(2)

sys.exit(0)
