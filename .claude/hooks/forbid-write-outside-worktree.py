#!/usr/bin/env python3
# PreToolUse(Edit|Write|NotebookEdit) guard against cross-boundary writes.
#
# Two cases, decided by where the caller stands:
#   1. cwd inside .claude/worktrees/<name>  -> every write into the main checkout is
#      blocked. Paths outside the repo (scratchpad, temp) stay allowed.
#   2. cwd in the main checkout, call comes from a sub-agent (agent_id present) and at
#      least one worktree is registered -> writes into the main checkout are blocked, but
#      a write that lands inside a registered worktree passes: that is not the main
#      checkout, and it is the only case 2 write a sub-agent can legitimately make. It
#      cannot cd its way out of this case, because Edit/Write report the session cwd and
#      a `cd` in a Bash call does not move it (2026-08-17).
#      This is the 2026-08-07 incident: a sub-agent does not inherit its parent's cd and
#      lands in the main checkout, indistinguishable from a legitimate session except for
#      agent_id.
#   3. anything else -> the guard stays out of the way.
#
# agent_id, not agent_type, is the discriminator: agent_type is also set for sessions
# started with --agent, which would wrongly catch a teamlead run.
#
# Exit 2 = block, stderr is shown to Claude.
# See docs/decisions/2026-08-13-0959-worktree-waechter-statt-projektverzeichnis-vergleich.md
import json
import os
import subprocess
import sys
from pathlib import Path

WORKTREE_BASE = (".claude", "worktrees")


def fail_open(*_):
    """A guard that cannot determine the geometry must not block real work."""
    sys.exit(0)


def target_path(tool_input):
    """Edit/Write carry file_path, NotebookEdit carries notebook_path."""
    return tool_input.get("file_path") or tool_input.get("notebook_path")


def main_checkout(cwd):
    """The main checkout, even when called from inside a worktree.

    git's common dir points at the main repo's .git from every worktree, so its parent is
    the main checkout. CLAUDE_PROJECT_DIR is only the fallback: it is whatever directory
    Claude Code was started in, which is not guaranteed to be the main checkout.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip()).resolve().parent
    except (OSError, subprocess.SubprocessError):
        pass

    fallback = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(fallback).resolve() if fallback else None


def containing_worktree(cwd, base):
    """The worktree directory cwd sits in, or None if cwd is not inside one."""
    if not cwd.is_relative_to(base):
        return None
    return base / cwd.relative_to(base).parts[0]


def registered_worktrees(root, base):
    """git is authoritative here: a leftover directory is not an active worktree."""
    try:
        out = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if out.returncode != 0:
        return []
    listed = (
        Path(line[len("worktree ") :].strip()).resolve()
        for line in out.stdout.splitlines()
        if line.startswith("worktree ")
    )
    return [path for path in listed if path.is_relative_to(base)]


def block(message):
    sys.stderr.write(message)
    sys.exit(2)


try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    fail_open()

target = target_path(data.get("tool_input") or {})
if not target:
    fail_open()

raw_cwd = data.get("cwd") or os.getcwd()
try:
    # resolve() follows the junctions worktree-erstellen creates, so a write that reaches
    # the main checkout through .claude/skills is judged by where it actually lands.
    cwd = Path(raw_cwd).resolve()
    target = Path(target)
    target = (target if target.is_absolute() else cwd / target).resolve()
except OSError:
    fail_open()

root = main_checkout(cwd)
if root is None:
    fail_open()

base = root.joinpath(*WORKTREE_BASE)
if not target.is_relative_to(root):
    sys.exit(0)  # outside the repo entirely: scratchpad, temp, anywhere else

worktree = containing_worktree(cwd, base)

if worktree is not None:
    if not target.is_relative_to(worktree):
        block(
            f"Blockiert: Schreibzugriff aus dem Worktree in den Haupt-Checkout.\n"
            f"  Arbeitsverzeichnis: {cwd}\n"
            f"  Ziel:               {target}\n"
            f"Wer in einem Worktree arbeitet, schreibt ausschliesslich dort. "
            f"Wechsle mit 'cd {worktree}' und schreibe unterhalb dieses Pfades. "
            f"Pfade ausserhalb des Repos (Scratchpad, Temp) sind frei.\n"
        )
    sys.exit(0)

worktrees = registered_worktrees(root, base)

if data.get("agent_id") and worktrees:
    if any(target.is_relative_to(path) for path in worktrees):
        sys.exit(0)  # lands in a worktree, so not the main checkout
    block(
        f"Blockiert: Sub-Agent schreibt in den Haupt-Checkout, waehrend ein Worktree "
        f"offen ist.\n"
        f"  Ziel: {target}\n"
        f"Ein Sub-Agent erbt das Arbeitsverzeichnis seines Elternteils nicht und landet "
        f"im Haupt-Checkout. Wechsle zuerst explizit in den zugewiesenen Worktree unter "
        f"{base} und wiederhole den Schreibzugriff von dort. "
        f"Siehe docs/decisions/2026-08-07-1416-incident-subagent-schreibt-im-haupt-checkout.md\n"
    )

sys.exit(0)
