#!/usr/bin/env python3
"""Smart PreToolUse hook for Claude Code.

Decomposes compound bash commands (&&, ||, ;, |, $(), newlines) into
individual sub-commands and checks each against the allow/deny patterns
in ~/.claude/settings.json.

Source: https://github.com/liberzon/claude-hooks
Author: Yair Liberzon
License: MIT

Input:  JSON on stdin with tool_name and tool_input.command
Output: JSON with {"decision": "allow"/"deny", "reason": "..."} or silent exit
"""

import fnmatch
import json
import os
import re
import sys
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Settings loading
# ---------------------------------------------------------------------------

def load_settings(path=None):
    """Load and return the permissions dict from settings.json."""
    if path is None:
        path = os.path.expanduser("~/.claude/settings.json")
    path = os.path.expanduser(path)
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_merged_settings(global_path=None):
    """Load and merge all settings layers matching Claude Code's behavior.

    Loads up to three sources and merges their permissions.allow/deny arrays:
      1. Global:        ~/.claude/settings.json (or $CLAUDE_SETTINGS_PATH)
      2. Project:       $CLAUDE_PROJECT_DIR/.claude/settings.json (committed)
      3. Project-local: $CLAUDE_PROJECT_DIR/.claude/settings.local.json (gitignored)
    """
    settings = load_settings(global_path)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir:
        return settings

    project_shared = load_settings(
        os.path.join(project_dir, ".claude", "settings.json")
    )
    project_local = load_settings(
        os.path.join(project_dir, ".claude", "settings.local.json")
    )

    if not project_shared and not project_local:
        return settings

    global_perms = settings.get("permissions", {})
    shared_perms = project_shared.get("permissions", {})
    local_perms = project_local.get("permissions", {})

    merged_allow = list(dict.fromkeys(
        global_perms.get("allow", [])
        + shared_perms.get("allow", [])
        + local_perms.get("allow", [])
    ))
    merged_deny = list(dict.fromkeys(
        global_perms.get("deny", [])
        + shared_perms.get("deny", [])
        + local_perms.get("deny", [])
    ))

    settings.setdefault("permissions", {})
    settings["permissions"]["allow"] = merged_allow
    settings["permissions"]["deny"] = merged_deny

    return settings


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------

class BashPattern(NamedTuple):
    """A parsed Bash permission pattern: command prefix and its fnmatch glob."""
    prefix: str
    glob: str


def parse_bash_patterns(patterns):
    """Extract command prefixes from Bash(...) permission patterns.

    "Bash(git status:*)" -> BashPattern(prefix="git status", glob="git status *")
    "Bash(rm:*)"         -> BashPattern(prefix="rm", glob="rm *")
    Non-Bash patterns are skipped.
    """
    result = []
    for pat in patterns:
        m = re.match(r'^Bash\((.+)\)$', pat)
        if not m:
            continue
        inner = m.group(1)
        colon_idx = inner.find(':')
        if colon_idx == -1:
            result.append(BashPattern(prefix=inner, glob=inner))
        else:
            prefix = inner[:colon_idx]
            suffix = inner[colon_idx + 1:]
            glob_pat = prefix + ' ' + suffix if suffix else prefix
            result.append(BashPattern(prefix=prefix, glob=glob_pat))
    return result


def command_matches_pattern(cmd, patterns):
    """Check if a command matches any of the parsed Bash patterns."""
    for bp in patterns:
        if cmd == bp.prefix:
            return True
        if fnmatch.fnmatch(cmd, bp.glob):
            return True
    return False


# ---------------------------------------------------------------------------
# Shell parsing
# ---------------------------------------------------------------------------

class _ShellCursor:
    """Quoting and paren-depth state for character-by-character shell parsing.

    Callers drive the iteration loop and manage the position index themselves.
    This object holds shared quoting/depth state and exposes mutation helpers
    so that split_on_operators (and similar future parsers) do not need to
    inline the same three state variables.

    Depth is incremented by $(, <(, >(, and bare ( — all are valid subshell
    or process-substitution openers that must not be split across at top level.
    """

    __slots__ = ('in_sq', 'in_dq', 'depth')

    def __init__(self) -> None:
        self.in_sq: bool = False    # currently inside single quotes
        self.in_dq: bool = False    # currently inside double quotes
        self.depth: int = 0         # subshell / group paren nesting depth

    @property
    def at_top_level(self) -> bool:
        """True when not inside any quotes or subshell parens."""
        return not self.in_sq and not self.in_dq and self.depth == 0

    def toggle_single_quote(self) -> None:
        self.in_sq = not self.in_sq

    def toggle_double_quote(self) -> None:
        self.in_dq = not self.in_dq

    def open_paren(self) -> None:
        self.depth += 1

    def close_paren(self) -> None:
        if self.depth > 0:
            self.depth -= 1


def extract_subshells(command):
    """Extract contents of executable substitutions, recursively.

    Returns a list of substitution content strings.

    Known limitations:
    - Backtick expressions are found by simple even/odd split; escaped
      backticks (\\`) inside backtick strings are not handled correctly.
    - $(...) and <(...)/>(...) inside single-quoted strings are included even
      though bash does not expand them there.
    """
    subshells = []

    i = 0
    while i < len(command):
        if command[i] == '$' and i + 1 < len(command) and command[i + 1] == '(' \
                and not (i + 2 < len(command) and command[i + 2] == '('):
            depth = 0
            start = i + 2
            j = i + 1
            while j < len(command):
                if command[j] == '(':
                    depth += 1
                elif command[j] == ')':
                    depth -= 1
                    if depth == 0:
                        content = command[start:j]
                        subshells.append(content)
                        subshells.extend(extract_subshells(content))
                        break
                j += 1
            i = j + 1
            continue

        if command[i] in ('<', '>') and i + 1 < len(command) and command[i + 1] == '(':
            depth = 0
            start = i + 2
            j = i + 1
            while j < len(command):
                if command[j] == '(':
                    depth += 1
                elif command[j] == ')':
                    depth -= 1
                    if depth == 0:
                        content = command[start:j]
                        subshells.append(content)
                        subshells.extend(extract_subshells(content))
                        break
                j += 1
            i = j + 1
            continue

        i += 1

    # Backtick substitutions: odd-indexed parts between backticks.
    # Note: escaped backticks (\\`) are not handled; this is a known limitation.
    parts = command.split('`')
    for idx in range(1, len(parts), 2):
        content = parts[idx]
        if content.strip():
            subshells.append(content)
            subshells.extend(extract_subshells(content))

    return subshells


def strip_heredocs(command):
    """Strip heredoc bodies from a command, leaving just the <<DELIM marker.

    Heredocs like <<'EOF'\\n...\\nEOF are replaced with the marker only
    (body removed).  This prevents heredoc content lines from being treated
    as sub-commands when we split on newlines.
    """
    lines = command.split('\n')
    result = []
    heredoc_delim = None
    i = 0

    while i < len(lines):
        if heredoc_delim is not None:
            if lines[i].strip() == heredoc_delim:
                heredoc_delim = None
            i += 1
            continue

        m = re.search(r'<<-?\s*[\'"]?(\w+)[\'"]?', lines[i])
        if m:
            heredoc_delim = m.group(1)

        result.append(lines[i])
        i += 1

    return '\n'.join(result)


def split_on_operators(command):
    """Split a command string on &&, ||, ;, |, and newlines.

    Respects quoted strings and all subshell / group paren constructs:
    $(...), <(...), >(...), and bare (...) grouping.  Does not split inside
    any of these.  Returns the top-level command segments.
    """
    command = strip_heredocs(command)
    command = command.replace('\\\n', ' ')

    segments = []
    current = []
    cur = _ShellCursor()
    i = 0

    while i < len(command):
        ch = command[i]

        # Backslash escape: consume two chars, no state change.
        # Inside single quotes \\ is literal — don't consume the next char there.
        if ch == '\\' and not cur.in_sq and i + 1 < len(command):
            current.append(ch)
            current.append(command[i + 1])
            i += 2
            continue

        # Single-quote toggle (only outside double quotes and subshells)
        if ch == "'" and not cur.in_dq and cur.depth == 0:
            cur.toggle_single_quote()
            current.append(ch)
            i += 1
            continue

        # Double-quote toggle (only outside single quotes and subshells)
        if ch == '"' and not cur.in_sq and cur.depth == 0:
            cur.toggle_double_quote()
            current.append(ch)
            i += 1
            continue

        # Inside any quote: pass through verbatim
        if cur.in_sq or cur.in_dq:
            current.append(ch)
            i += 1
            continue

        # $(, <(, >( open a subshell or process substitution — consume both chars
        if ch in ('$', '<', '>') and i + 1 < len(command) and command[i + 1] == '(':
            cur.open_paren()
            current.append(ch)
            current.append('(')
            i += 2
            continue

        # Bare ( opens a subshell group, e.g. (cd /tmp && ls)
        if ch == '(':
            cur.open_paren()
            current.append(ch)
            i += 1
            continue

        # ) closes whatever opened the current depth level
        if ch == ')' and cur.depth > 0:
            cur.close_paren()
            current.append(ch)
            i += 1
            continue

        # Inside any subshell / group: pass through
        if cur.depth > 0:
            current.append(ch)
            i += 1
            continue

        # At top level: check compound operators first (&&, ||), then single-char
        if ch == '&' and i + 1 < len(command) and command[i + 1] == '&':
            segments.append(''.join(current))
            current = []
            i += 2
            continue
        if ch == '|' and i + 1 < len(command) and command[i + 1] == '|':
            segments.append(''.join(current))
            current = []
            i += 2
            continue
        if ch in (';', '|', '\n'):
            segments.append(''.join(current))
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    segments.append(''.join(current))
    return [s.strip() for s in segments if s.strip()]


def _skip_shell_value(cmd, i):
    """Skip past one shell 'word' value starting at position i.

    Handles quoted strings, $() subshells (tracking paren depth), and
    bare non-whitespace runs.  Returns the index just past the value.
    """
    if i >= len(cmd):
        return i

    if cmd[i] == '"':
        i += 1
        while i < len(cmd) and cmd[i] != '"':
            if cmd[i] == '\\' and i + 1 < len(cmd):
                i += 2
            else:
                i += 1
        if i < len(cmd):
            i += 1  # skip closing quote
        return i
    if cmd[i] == "'":
        i += 1
        while i < len(cmd) and cmd[i] != "'":
            i += 1
        if i < len(cmd):
            i += 1  # skip closing quote
        return i

    # Unquoted value — consume non-whitespace, tracking $() depth
    paren_depth = 0
    while i < len(cmd):
        ch = cmd[i]
        if ch == '$' and i + 1 < len(cmd) and cmd[i + 1] == '(':
            paren_depth += 1
            i += 2
            continue
        if ch == '(' and paren_depth > 0:
            paren_depth += 1
            i += 1
            continue
        if ch == ')' and paren_depth > 0:
            paren_depth -= 1
            i += 1
            continue
        if paren_depth > 0:
            i += 1
            continue
        if ch in (' ', '\t'):
            break
        i += 1
    return i


def strip_env_vars(cmd):
    """Strip leading environment variable assignments (FOO=bar cmd ...).

    Returns the command with env var prefixes removed.
    Correctly handles values containing $() subshells.
    """
    while True:
        m = re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', cmd)
        if not m:
            break
        i = _skip_shell_value(cmd, m.end())
        rest = cmd[i:].lstrip()
        if not rest:
            break
        cmd = rest
    return cmd


def strip_redirections(cmd):
    """Strip output/input redirections from a command.

    Removes patterns like >file, >>file, 2>&1, <file, etc.
    Note: applied after top-level splitting, so quoted redirection-like
    strings are typically already separated.
    """
    cmd = re.sub(r'\d*>>?\s*&?\d*\S*', '', cmd)
    cmd = re.sub(r'<<<?\s*\S+', '', cmd)
    cmd = re.sub(r'<\s*\S+', '', cmd)
    return cmd.strip()


# Shell keywords that are structural, not commands to approve/deny.
SHELL_KEYWORDS = frozenset({
    'do', 'done', 'then', 'else', 'elif', 'fi', 'esac', '{', '}',
    'break', 'continue',
})

# Keywords that can prefix a command when joined by ; (e.g. "do echo hello").
_KEYWORD_PREFIX_RE = re.compile(r'^(do|then|else|elif)\s+')

# Patterns for shell compound statement headers (for, while, until, if, case).
_COMPOUND_HEADER_RE = re.compile(r'^(for|while|until|if|case|select)\b')


def strip_keyword_prefix(cmd):
    """Strip leading shell keyword prefix from a command.

    "do echo hello" -> "echo hello"
    "then git status" -> "git status"
    """
    m = _KEYWORD_PREFIX_RE.match(cmd)
    if m:
        return cmd[m.end():]
    return cmd


def is_shell_structural(cmd):
    """Return True if cmd is a shell keyword or compound-statement header."""
    if cmd in SHELL_KEYWORDS:
        return True
    if _COMPOUND_HEADER_RE.match(cmd):
        return True
    return False


def is_standalone_assignment(cmd):
    """Return True if cmd is purely a variable assignment (no following command).

    e.g. "result=$(curl ...)" or "FOO=bar" — these are not commands to check.
    The subshell contents, if any, are extracted and checked separately.
    """
    m = re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', cmd)
    if not m:
        return False
    end = _skip_shell_value(cmd, m.end())
    rest = cmd[end:].strip()
    return rest == ''


def normalize_command(cmd):
    """Normalize a command by stripping env vars, redirections, and whitespace."""
    cmd = cmd.strip()
    if not cmd:
        return cmd
    cmd = strip_keyword_prefix(cmd)
    cmd = strip_env_vars(cmd)
    cmd = strip_redirections(cmd)
    cmd = re.sub(r'\s+', ' ', cmd)
    return cmd.strip()


def decompose_command(command):
    """Decompose a compound command into all individual sub-commands.

    Splits on operators, extracts subshell contents, normalizes each.
    Filters out shell structural keywords (for/do/done/etc.) and
    standalone variable assignments (whose subshell contents are checked
    separately).
    Returns a list of normalized command strings.
    """
    all_commands = []

    segments = split_on_operators(command)

    for seg in segments:
        subshells = extract_subshells(seg)
        for sub in subshells:
            sub_segments = split_on_operators(sub)
            for ss in sub_segments:
                normalized = normalize_command(ss)
                if normalized:
                    all_commands.append(normalized)

        normalized = normalize_command(seg)
        if normalized:
            all_commands.append(normalized)

    return [
        cmd for cmd in all_commands
        if not is_shell_structural(cmd) and not is_standalone_assignment(cmd)
    ]


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------

def decide(sub_commands, settings):
    """Make a permission decision for a pre-decomposed list of sub-commands.

    Returns:
        ("allow", reason) if all sub-commands match allow patterns
        ("deny",  reason) if any sub-command matches a deny pattern
        (None, None)      to fall through to normal prompting
    """
    if not sub_commands:
        return None, None

    permissions = settings.get("permissions", {})
    allow_patterns = parse_bash_patterns(permissions.get("allow", []))
    deny_patterns = parse_bash_patterns(permissions.get("deny", []))

    for cmd in sub_commands:
        if command_matches_pattern(cmd, deny_patterns):
            return "deny", f"Sub-command '{cmd}' matches deny pattern"

    if all(command_matches_pattern(cmd, allow_patterns) for cmd in sub_commands):
        return "allow", "All sub-commands match allow patterns"

    return None, None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    verbose = os.environ.get("SMART_APPROVE_VERBOSE", "").lower() in ("1", "true", "yes")
    logs = []

    def log(msg):
        if verbose:
            logs.append(msg)

    cmd_preview = command[:80].replace('\n', '\\n')
    log(f"checking: {cmd_preview}{'...' if len(command) > 80 else ''}")

    settings_path = os.environ.get("CLAUDE_SETTINGS_PATH")
    settings = load_merged_settings(settings_path)

    sub_commands = decompose_command(command)
    log(f"sub-commands: {sub_commands[:5]}{'...' if len(sub_commands) > 5 else ''}")

    decision, reason = decide(sub_commands, settings)

    log(f"decision={decision or 'passthrough'} reason={reason or 'no pattern matched'}")

    if decision is not None:
        full_reason = f"{reason} | {' | '.join(logs)}" if logs else reason
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": full_reason,
            }
        }
        json.dump(output, sys.stdout)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
