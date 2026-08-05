#!/usr/bin/env python3
# PreToolUse(Edit|Write) nudge: on every C# edit, reminds Claude to prefer declarative
# LINQ over imperative transformation loops. Exit 0 = allow (always); only injects
# additionalContext to guide behavior. Nudge, not block — see docs/issues/0007.
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input, cs_file_path

data = load_hook_input()
cs_file_path(data)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": (
            "Deklarativ-Nudge: Eine `foreach`, deren Body eine reine Transformation ist "
            "(input -> output sammeln, z.B. einziges Statement ist `.Add(...)`/`.Append(...)`), "
            "ist eine verkappte Map, kein Control-Flow. Bevorzuge die deklarative Form:\n"
            "  ctx.Messages.AddRange(rows.Select(r => new MessageRow { ... }));\n"
            "Sieht der Body unsauber aus, zieh die reine Abbildung als Funktion `T -> R` raus - "
            "dann wird daraus `src.Select(Map)`.\n"
            "Imperativ BLEIBEN: echte Seiteneffekte (void pro Element), `await` (foreach ist "
            "sequenziell, `Task.WhenAll(Select(...))` waere parallel = andere Semantik), "
            "`break`/`continue`/early-return, Cross-Iteration-State (Akkumulator), Perf-Hotpath. "
            "Torture LINQ nicht in den Job einer Schleife. "
            "Siehe docs/issues/0007 und .rules/csharp/csharp-control-flow.md."
        )
    }
}))

sys.exit(0)
