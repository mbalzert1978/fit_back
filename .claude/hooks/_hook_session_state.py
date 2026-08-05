#!/usr/bin/env python3
# Session-local state for hooks: session-id resolution and JSON state persistence.
# Session-id lookup order (stdin session_id, then CLAUDE_SESSION_ID env, else "default")
# and the tempfile.gettempdir()-based storage location follow suggest-compact.py's pattern
# (see suggest-compact.py:23-38) — reproduced here, not imported, since suggest-compact.py
# itself must stay unchanged. State is process/session-local only and may be discarded at
# session end; there is no cross-session persistence here.
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import sanitize_session_id  # reuse the one robust sanitizer instead of a second regex


def resolve_session_id(data):
    """Resolves the session id from an already-parsed hook payload (hooks consume stdin
    once via load_hook_input, so this takes `data` rather than re-reading stdin)."""
    session_id = data.get("session_id")
    if not (isinstance(session_id, str) and session_id):
        session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    return sanitize_session_id(session_id) or "default"


def _state_file(session_id):
    return Path(tempfile.gettempdir()) / f"claude-csharp-rules-state-{session_id}.json"


def load_state(session_id):
    try:
        loaded = json.loads(_state_file(session_id).read_text(encoding="utf-8"))
        return {
            "gelesene_regeln": loaded.get("gelesene_regeln", []),
            "pro_ziel": loaded.get("pro_ziel", {}),
        }
    except Exception:
        return {"gelesene_regeln": [], "pro_ziel": {}}


def save_state(session_id, state):
    try:
        _state_file(session_id).write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


def record_regel_read(session_id, regel_dateiname):
    """Marks a .rules/ file as read this session (called from the Read-tracking hook)."""
    state = load_state(session_id)
    if regel_dateiname not in state["gelesene_regeln"]:
        state["gelesene_regeln"].append(regel_dateiname)
        save_state(session_id, state)


def record_edit_and_should_remind(session_id, ziel, threshold=5):
    """Per-target reminder throttle (state schema's `pro_ziel`, CLAUDE.md-documented).

    First hit for a target always reminds and starts its counter at 0. A later hit on the
    *same* target increments its own counter and only reminds again once that counter
    reaches `threshold` (then resets to 0). Hits on other targets never affect this one.
    """
    state = load_state(session_id)
    pro_ziel = state["pro_ziel"]
    entry = pro_ziel.get(ziel)

    if entry is None:
        pro_ziel[ziel] = {"edits_seit_letztem_reminder": 0}
        save_state(session_id, state)
        return True

    count = entry.get("edits_seit_letztem_reminder", 0) + 1
    if count >= threshold:
        entry["edits_seit_letztem_reminder"] = 0
        remind = True
    else:
        entry["edits_seit_letztem_reminder"] = count
        remind = False
    save_state(session_id, state)
    return remind
