#!/usr/bin/env python3
# PreToolUse(Bash) guard: blocks bare ls calls, enforces eza.
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input, bash_command

data = load_hook_input()

BSP = r"""
# eza Quick Reference (LLM-optimized)

## Invocation forms
eza                     # grid view of current directory
eza DIR                 # grid view of DIR
eza FILE …              # list specific files
eza -l                  # long/table view
eza -T                  # tree view (recursive)
eza -lT                 # long tree (metadata on every node)
eza -lG                 # grid-details (multi-column long view)

## View modes
eza          Grid (default)   — grid::Render
eza -l       Details/Table    — details::Render
eza -1       Lines (one/line) — lines::Render
eza -lG      GridDetails      — grid_details::Render
eza -T       Tree             — TreeTrunk

-G / --grid         force grid view even when piped
-l / --long         long/details view (permissions, owner, size, time)
-1 / --oneline      one file per line
-T / --tree         recurse into directories as a tree

## Listing flags
-a / --all           show hidden files (dot-files); use twice (-aa) for . and ..
-d / --list-dirs     list directories themselves, not their contents
-r / --recurse       recurse into directories (flat listing, not tree)
-L N / --level N     limit recursion depth (with -T or -r)
-x / --across        sort grid entries across rather than downward

## Long-view columns (-l)
-h / --human-readable   sizes as 1K, 2M, etc.
-b / --binary           sizes as powers of 1024 (KiB, MiB)
-B / --bytes            sizes as raw byte counts
-g / --group            show group name column
-H / --links            show hard-link count
-i / --inode            show inode number
-n / --numeric          show UID/GID as numbers instead of names
-S / --blocksize        show allocated block size
-@ / --extended         show extended attributes (xattr)
-Z / --context          show SELinux/AppArmor security context
--time-style STYLE      date format: default | iso | long-iso | full-iso | relative

## Metadata / decoration flags
--icons / --icons=auto/always/never   prepend file-type glyphs
-F / --classify                       append type indicator: / dir, @ symlink, * exec, | pipe
--color / --colour=auto/always/never  colorize output
--hyperlinks                          make filenames OSC-8 terminal hyperlinks

## Git integration
--git                 show per-file Git status column
--git-ignore          hide files that match .gitignore rules
# Git status chars: N=new, M=modified, D=deleted, R=renamed, T=typechange, I=ignored

## Sorting (-s / --sort)
-s name       sort by filename (default)
-s size       sort by file size (largest first)
-s extension  sort by file extension
-s modified   sort by modification time
-s accessed   sort by access time
-s created    sort by creation time
-s type       sort directories first
-s none       no sorting (filesystem order)
-r / --reverse  reverse sort order (combine with -s)

## Filtering
-I GLOB / --ignore-glob GLOB   exclude files matching glob
--only-dirs / -D               show only directories
--only-files                   show only files

## Common patterns
eza -la                          # ls -la equivalent
eza -T -L 3 --icons              # tree, depth 3, with icons
eza -la -h --git                 # long, human sizes, git status, hidden
eza -l -s size -h                # sort by size descending, human-readable
eza -rD                          # recurse, only dirs
eza -I 'node_modules'            # filter out node_modules
eza -lG                          # grid-details in wide terminal
eza -T --git                     # tree with git status
eza -la -s modified --reverse    # all files, newest first
"""

command = bash_command(data)

# Match `ls` as a standalone command token: at line start, after ; | & or whitespace.
# Avoids false positives on path segments like /usr/local/ls or variable names like $ls_output.
if re.search(r'(?:^|[;&|`\s])\s*ls(?:\s|$)', command):
    sys.stderr.write(
        "Blockiert: ls ist verboten. Nutze stattdessen eza — "
        "Git-Integration, Icons, bessere Spaltenformatierung.\n"
        f"Beispiel:{BSP}"
    )
    sys.exit(2)

sys.exit(0)
