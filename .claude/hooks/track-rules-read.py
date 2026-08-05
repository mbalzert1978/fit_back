#!/usr/bin/env python3
# PostToolUse(Read) tracker: records which .rules/ files were Read this session into the
# session-local state that csharp-rules-reminder.py's blocking gate consumes. Never blocks
# a Read itself (observer only) - exit 0 always.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input
from _hook_session_state import resolve_session_id, record_regel_read

data = load_hook_input()
path = ((data.get("tool_input") or {}).get("file_path") or "").replace("\\", "/")

if "/.rules/" in path.lower():
    record_regel_read(resolve_session_id(data), Path(path).name)

sys.exit(0)
