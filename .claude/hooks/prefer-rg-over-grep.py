#!/usr/bin/env python3
# PreToolUse guard: blocks grep (Bash) and the internal Grep tool; enforces ripgrep (rg).
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input

data = load_hook_input()

BSP = r"""
# ripgrep (rg) Quick Reference (LLM-optimized)

## Shell quoting (CRITICAL on Windows/Git Bash)
- Git Bash / Unix:   rg 'pattern' file    # single quotes around pattern
- PowerShell:        rg 'pattern' file    # single quotes, escape inner " as \"
- Escape regex meta: rg 'fn write\(' src  # or use -F for literal match

## Invocation forms
rg PATTERN              # recursive search in current dir (= rg PATTERN ./)
rg PATTERN FILE         # search single file
rg PATTERN DIR          # search directory
rg PATTERN -g '*.rs'    # restrict to glob
rg PATTERN -trust       # restrict to Rust files  (-t TYPE shorthand)

## Essential flags
-i / --ignore-case      case-insensitive match
-S / --smart-case       ignore case unless pattern has uppercase
-F / --fixed-strings    literal string, no regex
-w / --word-regexp      whole-word match only
-e PATTERN              explicit pattern (allows multiple -e flags)
-r / --replace TEXT     replace matched portion in output (never modifies files)
-o / --only-matching    print only the matched part
-c / --count            count matched lines per file
-l / --files-with-matches  print only filenames
-C N / --context N      N lines of context around each match
-U / --multiline        allow matches spanning multiple lines
-a / --text             search binary files as text (caution: NUL bytes)
--binary                binary mode: continue past NUL until match found
-L / --follow           follow symlinks
-M N / --max-columns N  truncate long lines (0 = unlimited, overrides config)
-z / --search-zip       search gzip/bzip2/xz/lz4/zstd compressed files
--files                 list files that *would* be searched
--sort path             sort output by filename (disables parallelism)
--debug                 show why files are ignored / what config is loaded
--no-config             ignore RIPGREP_CONFIG_PATH entirely

## Disabling auto-filters
--no-ignore             disable .gitignore / .ignore / .rgignore filtering
-.  / --hidden          include hidden files and directories
-u  / --unrestricted    disable .gitignore  (repeat: -uu adds hidden, -uuu adds binary)

## Glob filtering (-g)
rg PATTERN -g '*.toml'    # include only .toml files
rg PATTERN -g '!*.toml'   # exclude .toml files
-g flags compose: later globs override earlier ones

## File type filtering (--type / -t / -T)
rg PATTERN --type rust      # same as -trust
rg PATTERN --type-not rust  # same as -Trust
rg PATTERN -tc              # C files (*.c, *.h)
rg --type-list              # list all built-in types + globs
rg --type-add 'web:*.{html,css,js}' -tweb PATTERN   # define custom type
--type all                  # match any file type in --type-list

## Replacements
rg fast README.md -r FAST              # replace matched portion
rg '^.*fast.*$' README.md -r FAST      # replace whole matching line
rg fast README.md -or FAST             # -o (only-matching) + -r
rg 'fast\s+(\w+)' README.md -r 'fast-$1'          # numbered capture group
rg 'fast\s+(?P<word>\w+)' README.md -r 'fast-$word' # named capture group
# Note: --replace NEVER writes to files, only changes stdout

## Regex syntax essentials
\w      word character (Unicode-aware by default)
\s      whitespace
.       any Unicode codepoint (not byte in default mode)
\w+     one or more
\w*     zero or more
(?-u)   disable Unicode for next construct (matches raw bytes)
(?P<name>…)  named capturing group; reference as $name in -r

## Auto-filtering rules (default recursive search)
Ignored automatically:
  1. .gitignore globs (incl. global + repo-specific + parent dirs)
  2. .ignore globs (higher precedence than .gitignore)
  3. .rgignore globs (highest precedence)
  4. Hidden files/directories
  5. Binary files (contain NUL byte)
  6. Symlinks (not followed)

Override hierarchy (highest wins): .rgignore > .ignore > .gitignore
To whitelist a .gitignore path: add `!path/` to .ignore
Case-insensitive ignore files: --ignore-file-case-insensitive (performance cost)

## Configuration file
Set env var:  RIPGREP_CONFIG_PATH=$HOME/.ripgreprc
Format rules:
  - One shell argument per line (no escaping)
  - Lines starting with # (optionally indented) are comments
  - Flag+value: --max-columns=150  OR two lines: --max-columns \n 150
  - Config is prepended; CLI args override (last flag wins)

Example config:
  --max-columns=150
  --max-columns-preview
  --hidden
  --glob=!.git/*
  --smart-case
  --type-add
  web:*.{html,css,js}

## Binary file modes
Default  stop as soon as NUL detected during recursive traversal;
         warn if match already printed (explicit file args bypass this)
--binary continue past NUL until first match or EOF; then warn
-a/--text disable all binary detection; search raw bytes

## File encoding
Default (--encoding auto):
  - Assumes ASCII-compatible input (ASCII, latin1, UTF-8 all work)
  - BOM sniffing: UTF-16 BOM -> transcode to UTF-8 then search
  - \w, . etc. assume UTF-8; non-UTF-8 bytes won't match Unicode classes
-E/--encoding LABEL   force encoding for all files (+ BOM override)
-E none               raw bytes, no transcoding, no BOM sniffing

## Preprocessor (--pre)
rg --pre ./script PATTERN FILE
  - ripgrep runs: script FILE  (file path as $1, file on stdin)
  - script output is searched instead of raw file
  - use --pre-glob '*.pdf' to limit which files get preprocessed (huge speedup)

Example wrapper for PDF:
  #!/bin/sh
  case "$1" in
  *.pdf) [ -s "$1" ] && exec pdftotext - - || exec cat ;;
  *)     exec cat ;;
  esac

## Common patterns
# Find function definition
rg 'fn write\(' src

# Whole-word, case-insensitive
rg -wi 'error'

# Regex with capture + replace
rg '(\w+)\.GetById\((\w+)\)' -r '$1.FindAsync($2)'

# Count matches per file
rg -c PATTERN

# List files containing pattern
rg -l PATTERN

# Restrict to extension
rg PATTERN -g '*.{cs,fs}'

# Include hidden, ignore .gitignore
rg -. --no-ignore PATTERN

# Multiline match
rg -U 'start[\s\S]*?end' file

# Sort output (for reproducible diffs)
rg PATTERN --sort path
"""

tool_name = data.get("tool_name", "")

if tool_name == "Grep":
    ti = data.get("tool_input") or {}
    pattern = ti.get("pattern", "PATTERN")
    path    = ti.get("path", ".")
    glob    = ti.get("glob", "")
    rg_glob = f" -g '{glob}'" if glob else ""
    rg_cmd  = f"rg '{pattern}' {path}{rg_glob}"
    sys.stderr.write(
        "Blockiert: internes Grep-Tool verboten. Nutze stattdessen rg via Bash — "
        "respektiert .gitignore, Unicode-sicher, kein Kontext-Overhead.\n"
        f"Äquivalent: {rg_cmd}\n"
        f"Beispiel: {BSP}"
    )
    sys.exit(2)

if tool_name == "Bash":
    command = (data.get("tool_input") or {}).get("command", "")
    if re.search(r'(?:^|[;&|`\s])\s*(grep|egrep|fgrep)(?:\s|$)', command):
        sys.stderr.write(
            "Blockiert: grep ist verboten. Nutze stattdessen rg (ripgrep) — "
            "schneller, respektiert .gitignore, Unicode-sicher.\n"
            f"Beispiel: {BSP}"
        )
        sys.exit(2)

sys.exit(0)
