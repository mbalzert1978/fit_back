#!/usr/bin/env python3
# PreToolUse(Bash) guard: blocks find calls, enforces fd.
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input, bash_command

data = load_hook_input()
command = bash_command(data)

if re.search(r'(?:^|[;&|`\s])\s*find(?:\s|$)', command):
    sys.stderr.write(
        "Blockiert: find ist verboten. Nutze stattdessen fd — "
        ".gitignore-aware, schneller, intuitivere Syntax.\n"
        "Beispiel: fd -e cs statt find . -name '*.cs'\n"
    )
    sys.exit(2)

sys.exit(0)
