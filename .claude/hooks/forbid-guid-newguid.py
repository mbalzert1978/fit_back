#!/usr/bin/env python3
# PreToolUse(Edit|Write) guard: blocks Guid.NewGuid() in C# files.
# Standard: prefer Guid.CreateVersion7() (sortable v7 GUIDs) — see
# .rules/csharp/csharp-modern-syntax.md. Exit 2 = block, stderr is shown to Claude.
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input, cs_file_path, cs_new_fragments

data = load_hook_input()
cs_file_path(data)

if re.search(r"Guid\.NewGuid\s*\(", cs_new_fragments(data)):
    sys.stderr.write(
        "Blockiert: Guid.NewGuid() ist verboten. Nutze Guid.CreateVersion7() - "
        "zeit-sortierbare v7-GUIDs erhalten die Index-Lokalitaet bei Inserts. "
        "Siehe .rules/csharp/csharp-modern-syntax.md.\n"
    )
    sys.exit(2)

sys.exit(0)
