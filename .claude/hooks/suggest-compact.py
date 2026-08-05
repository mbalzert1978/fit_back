#!/usr/bin/env python3
"""
Strategic Compact Suggester

Cross-platform (Windows, macOS, Linux)

Runs on PreToolUse to suggest manual compaction at logical intervals.

Why manual over auto-compact:
- Auto-compact happens at arbitrary points, often mid-task
- Strategic compacting preserves context through logical phases
- Compact after exploration, before execution
- Compact after completing a milestone, before starting next
"""

import json
import os
import re
import sys
import tempfile


def resolve_session_id() -> str:
    try:
        data = json.load(sys.stdin)
        session_id = data.get("session_id", "")
        if isinstance(session_id, str) and session_id:
            return session_id
    except Exception:
        pass
    return os.environ.get("CLAUDE_SESSION_ID", "default")


def main() -> None:
    raw_session_id = resolve_session_id()
    session_id = re.sub(r"[^a-zA-Z0-9_-]", "", raw_session_id) or "default"

    counter_file = os.path.join(tempfile.gettempdir(), f"claude-tool-count-{session_id}")

    raw_threshold = os.environ.get("COMPACT_THRESHOLD", "50")
    try:
        threshold = int(raw_threshold)
        if not (0 < threshold <= 10000):
            threshold = 50
    except ValueError:
        threshold = 50

    count = 1

    try:
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY  # type: ignore[attr-defined]
        fd = os.open(counter_file, flags)
        try:
            raw = os.read(fd, 64).decode("utf-8", errors="replace").strip()
            if raw:
                try:
                    parsed = int(raw)
                    count = parsed + 1 if 0 < parsed <= 1_000_000 else 1
                except ValueError:
                    count = 1
            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, str(count).encode("utf-8"))
        finally:
            os.close(fd)
    except OSError:
        try:
            with open(counter_file, "w", encoding="utf-8") as f:
                f.write(str(count))
        except OSError:
            pass

    if count == threshold:
        msg = f"[StrategicCompact] {threshold} tool calls reached - consider /compact if transitioning phases"
        print(msg, file=sys.stderr)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg}}))

    if count > threshold and (count - threshold) % 25 == 0:
        msg = f"[StrategicCompact] {count} tool calls - good checkpoint for /compact if context is stale"
        print(msg, file=sys.stderr)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg}}))

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[StrategicCompact] Error: {e}", file=sys.stderr)
        sys.exit(0)
