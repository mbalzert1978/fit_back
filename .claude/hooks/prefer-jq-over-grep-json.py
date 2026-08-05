#!/usr/bin/env python3
# PreToolUse(Bash) guard: blocks grep/python/awk on *.json files, enforces jq.
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input, bash_command

data = load_hook_input()

BSP = r"""
# jq Quick Reference (LLM-optimized)

## Shell quoting (CRITICAL on Windows/Git Bash)
- Git Bash / Unix:   jq '.foo'          # single quotes around filter
- PowerShell:        jq '.foo'          # single quotes, escape inner " as \"
- cmd.exe:           jq ".foo"          # double quotes, inner " as \"

## Essential flags
-r   raw output (strings without JSON quotes)
-c   compact output (one line)
-n   no input (use when building JSON from scratch)
-e   exit 1 if result is false/null
-s   slurp all inputs into one array

## Basic filters
.              identity (pretty-print / validate)
.foo           field access
.foo.bar       chained field access
.["foo"]       field access with special chars
.[]            iterate all values
.[0]           array index (negative: .[-1] = last)
.[2:5]         array slice

## Pipe
.foo | .bar    same as .foo.bar
.[] | .name    get .name of each element

## Essential functions
keys            array of object keys (sorted)
has("k")        true if key exists
length          length of string/array/object/null
type            "null"|"boolean"|"number"|"string"|"array"|"object"
select(f)       keep only values where f is true
map(f)          apply f to each array element -> array
map_values(f)   apply f to each value (array or object)
to_entries      [{key,value},...] from object
from_entries    object from [{key,value},...]
with_entries(f) to_entries | map(f) | from_entries
del(.foo)       remove key
add             sum/concat array elements
any(f)          true if any element matches
all(f)          true if all elements match
sort_by(.f)     sort array by field
group_by(.f)    group array by field value
unique_by(.f)   deduplicate by field
first, last     first/last element
recurse(.f)     recursive descent
@base64, @uri, @csv, @tsv, @html   format strings

## Common patterns
# Extract field from each object in array
jq '.[].name' file.json

# Filter array where condition
jq '[.[] | select(.status == "active")]' file.json

# Get specific keys only
jq '{id: .id, name: .name}' file.json

# Count elements
jq '.items | length' file.json

# Flatten nested
jq '.[] | .items[]' file.json

# Build new structure
jq '.users[] | {(.id|tostring): .name}' file.json

# Multiple files
jq -s '.[0].key == .[1].key' a.json b.json

# Raw string value (no quotes)
jq -r '.name' file.json

# Conditional
jq 'if .count > 0 then .name else "empty" end' file.json

""" 

command = bash_command(data)

if re.search(r'\b(grep|awk|python3?\s+-c)\b.*\.json', command):
    sys.stderr.write(
        "Blockiert: grep/awk auf JSON-Dateien ist verboten. Nutze jq.\n"
        f"Beispiel: {BSP}"
    )
    sys.exit(2)

sys.exit(0)
