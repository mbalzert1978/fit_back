#!/usr/bin/env python3
import sys
import json


def load_hook_input():
    try:
        return json.load(sys.stdin)
    except Exception:
        sys.exit(0)


def bash_command(data):
    """Returns the Bash command string; exits 0 if the tool call is not Bash."""
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    return (data.get("tool_input") or {}).get("command", "")
