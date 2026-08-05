#!/usr/bin/env python3
# PreToolUse(Read) nudge: suggests bat (text/code) or jq (JSON); passes binary/special through.
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input

_PASS_THROUGH = {
    '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg',
    '.bmp', '.ico', '.tiff', '.ipynb',
}
_JSON = {'.json', '.jsonc', '.json5'}

data = load_hook_input()

if data.get("tool_name") != "Read":
    sys.exit(0)

ti        = data.get("tool_input") or {}
file_path = ti.get("file_path", "FILE")
offset    = ti.get("offset")
limit     = ti.get("limit")
ext       = Path(file_path).suffix.lower()

if ext in _PASS_THROUGH:
    sys.exit(0)

def nudge(msg: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": msg,
        }
    }))
    sys.exit(0)

if ext in _JSON:
    nudge(f"[Nudge] Für JSON lieber jq nutzen: jq . \"{file_path}\"")

# Build bat command with optional line range (bat -r is 1-based; offset is 0-based)
if offset is not None and limit is not None:
    range_flag = f" -r {int(offset) + 1}:{int(offset) + int(limit)}"
elif limit is not None:
    range_flag = f" -r :{int(limit)}"
elif offset is not None:
    range_flag = f" -r {int(offset) + 1}:"
else:
    range_flag = ""

nudge(f"[Nudge] Lieber bat nutzen: bat \"{file_path}\"{range_flag} --paging=never")
