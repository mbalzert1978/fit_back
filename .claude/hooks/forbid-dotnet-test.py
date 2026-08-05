#!/usr/bin/env python3
# PreToolUse(Bash) guard: blocks direct `dotnet test` invocations.
# Tests must go through the /run-tests skill (uv run scripts/run-tests.py),
# which locks in the one working MTP invocation. Exit 2 = block, stderr shown to Claude.
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input, bash_command

data = load_hook_input()
command = bash_command(data)

if re.search(r"\bdotnet\s+test\b", command):
    sys.stderr.write(
        "`dotnet test` ist in diesem Projekt nicht erlaubt. "
        "Nutze stattdessen den `/run-tests`-Skill.\n"
    )
    sys.exit(2)

sys.exit(0)
