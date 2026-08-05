#!/usr/bin/env python3
# PreToolUse(Edit|Write) reminder: on a C# edit, evaluates CLAUDE.md's C#-Regel-Trigger-
# Tabelle (via _hook_utils.evaluate_csharp_rule_signals) and names the concretely triggered
# .rules/ file(s)/section(s) instead of a generic pointer.
#
# If a triggered rule file was not yet Read this session (tracked by track-rules-read.py
# into the session-local state from _hook_session_state.py), this blocks (exit 2) — read
# first, then edit. Once all triggered files have been read, it falls back to an
# informational reminder, throttled per-target so the same target doesn't nag every edit
# (see _hook_session_state.record_edit_and_should_remind).
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input, cs_file_path, cs_new_fragments, evaluate_csharp_rule_signals
from _hook_session_state import resolve_session_id, load_state, record_edit_and_should_remind

REMINDER_THRESHOLD = 5

data = load_hook_input()
path = cs_file_path(data)
fragments = cs_new_fragments(data)

targets = evaluate_csharp_rule_signals(path, fragments)

if not targets:
    sys.exit(0)

session_id = resolve_session_id(data)
state = load_state(session_id)
gelesene_regeln = set(state["gelesene_regeln"])

required_files = sorted({t.split("#", 1)[0] for t in targets})
ungelesen = [f for f in required_files if f not in gelesene_regeln]

if ungelesen:
    sys.stderr.write(
        "Blockiert: dieser C#-Edit trifft ein Signal aus CLAUDE.mds "
        "C#-Regel-Trigger-Tabelle, aber " + ", ".join(ungelesen) + " wurde in dieser "
        "Session noch nicht gelesen. Erst lesen, dann editieren. Getroffene Abschnitte:\n"
        + "\n".join(f"  - {t}" for t in targets) + "\n"
    )
    sys.exit(2)

to_remind = [
    t for t in targets
    if record_edit_and_should_remind(session_id, t, REMINDER_THRESHOLD)
]

if to_remind:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": (
                "C#-Edit trifft folgende Regel-Abschnitte (CLAUDE.md, "
                "C#-Regel-Trigger-Tabelle) - vor dem Schreiben gegenpruefen: "
                + "; ".join(to_remind)
            )
        }
    }))

sys.exit(0)
