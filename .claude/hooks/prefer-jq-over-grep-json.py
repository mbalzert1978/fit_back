#!/usr/bin/env python3
# PreToolUse(Bash) nudge: fuer JSON gibt es kein Harness-Tool, also bleibt die Shell der Weg -
# aber grep/awk lesen JSON zeilenweise und zerschneiden Struktur. Exit 0 = immer erlauben;
# der Hook schiebt nur Kontext nach. Nudge statt Blocker - siehe Issue #18.
import sys, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input, bash_command

data = load_hook_input()
command = bash_command(data)

if re.search(r'\b(grep|awk|python3?\s+-c)\b.*\.json', command):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": (
                "jq-Nudge: grep/awk lesen JSON zeilenweise und sehen seine Struktur nicht - "
                "was ueber mehrere Zeilen steht oder verschachtelt liegt, faellt durch. "
                "`jq` fragt dieselbe Datei strukturiert ab und ist hier fast immer die kuerzere "
                "und verlaesslichere Route.\n"
                "  jq -r '.[] | select(.status == \"active\") | .name' datei.json"
            )
        }
    }))

sys.exit(0)
