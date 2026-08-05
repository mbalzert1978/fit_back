#!/usr/bin/env python3
# PreToolUse(Bash) guard: blocks sed s/// substitution calls, enforces sd.
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input, bash_command

data = load_hook_input()

BSP = r"""
# sd Quick Reference (LLM-optimized)

## Invocation forms
sd 'FIND' 'REPLACE'              # stdin -> stdout
sd 'FIND' 'REPLACE' FILE…        # in-place replacement in files (MODIFIES files)
echo 'text' | sd 'old' 'new'     # pipe mode

## Essential flags
-s / --string-mode    literal string, no regex (like rg -F)
-f FLAGS              regex flags: i=case-insensitive, m=multiline, s=dot-all, u=Unicode
-p / --preview        show diff without modifying files

## Capture groups
sd '(\w+) (\w+)' '$2 $1'            # numbered groups
sd '(?P<a>\w+) (?P<b>\w+)' '$b $a'  # named groups

## Common patterns
sd -s 'old.text' 'new text' file.txt            # literal replace
sd 'GetById\((\w+)\)' 'FindAsync($1)' **/*.cs   # regex + capture
sd -f i 'todo' 'DONE' notes.txt                 # case-insensitive
sd -p 'foo' 'bar' file.txt                      # preview diff first
sd ' +$' '' **/*.cs                             # strip trailing whitespace
rg -l 'OldName' | xargs sd 'OldName' 'NewName' # rg find + sd replace

## sd vs sed cheatsheet
sed 's/foo/bar/g' file        ->  sd 'foo' 'bar' file
sed 's/foo/bar/gi' file       ->  sd -f i 'foo' 'bar' file
sed -i 's/foo/bar/g' file     ->  sd 'foo' 'bar' file   (always in-place)
sed 's/\(a\)\(b\)/\2\1/'      ->  sd '(a)(b)' '$2$1'    (no backslash groups)
echo 'x' | sed 's/x/y/'      ->  echo 'x' | sd 'x' 'y'

## Notes
- sd uses Rust regex (same engine as rg); no delimiter escaping needed
- Always replaces all matches (no /g flag required)
- Files modified atomically; use -p to preview before applying
- No backup flag: rely on git or --preview
"""

command = bash_command(data)

# Match sed only when used for substitution (s/…/…/) or in-place (-i).
# Avoids blocking sed in comments, paths, or non-substitution usage (e.g. sed -n 'Np').
# We block: bare `sed`, `sed -i`, `sed -e 's/…'`, `sed 's/…'`
sed_match = re.search(r'(?:^|[;&|`\s])\s*sed\b', command)
sed_subst  = re.search(r"\bsed\b.*'[^']*s[/|,!][^']*'", command)  # sed with s/// expression
sed_inplace = re.search(r'\bsed\s+-[a-zA-Z]*i', command)           # sed -i (in-place)

if sed_subst or sed_inplace:
    sys.stderr.write(
        "Blockiert: sed (Substitution/In-Place) ist verboten. Nutze stattdessen sd — "
        "einfachere Regex-Syntax, kein Delimiter-Escaping, atomisches In-Place-Schreiben.\n"
        f"Beispiel:{BSP}"
    )
    sys.exit(2)

sys.exit(0)
