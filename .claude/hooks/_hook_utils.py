#!/usr/bin/env python3
import sys
import json
import re


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


def cs_file_path(data):
    """Exits 0 if the edited file is not a .cs file; returns the lowercased path."""
    path = ((data.get("tool_input") or {}).get("file_path") or "").lower()
    if not path.endswith(".cs"):
        sys.exit(0)
    return path


def cs_new_fragments(data):
    """Returns joined new-content fragments: Write.content + Edit.new_string + MultiEdit edits."""
    ti = data.get("tool_input") or {}
    parts = [ti.get("content") or "", ti.get("new_string") or ""]
    parts += [e.get("new_string") or "" for e in (ti.get("edits") or [])]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# C# rule-signal evaluation.
# Single source of truth: CLAUDE.md, section "C#-Regel-Trigger-Tabelle".
# Keep this function and that table in sync when either changes.
# ---------------------------------------------------------------------------

_ANTI_ANEMIC_OBJECT_CALLS_PORT = "anti-anemic-domain.md#Object-Calls-Port Pattern"
_RESULT_SHAPE = (
    'csharp-error-handling.md#A Shared Result<T, E> for the Binary "Value or Failure" Shape'
)
_PARSE_VS_HYDRATE = (
    "csharp-error-handling.md#Two Factories per Value Object: Fallible Parse vs. Infallible Hydrate"
)

_PARSE_OR_HYDRATE_DEF_RE = re.compile(r"\b(Parse|Hydrate)\s*\(\s*string\b")
_OK_CASE_RE = re.compile(r"\bsealed record (Ok|Success|Erfolg|Gefunden|Found)\w*\s*\(")
_FEHLER_CASE_RE = re.compile(
    r"\bsealed record (Fehler|Error|Failed|Failure|NichtGefunden|NotFound)\w*\s*\("
)
_CALLER_PATTERN_MATCH_RE = re.compile(r"\bis\s+\w*(Result|Fehler|Error|Status|Ergebnis)\.\w+")


def evaluate_csharp_rule_signals(path, fragments):
    """Matches CLAUDE.md's C#-Regel-Trigger-Tabelle against a C# edit's path and new content.

    Returns a deduped list of hit targets, each formatted "regel-datei.md#Abschnitt", in
    table order. Called by both the informational reminder and the session-local blocking
    gate in csharp-rules-reminder.py — one evaluation step, not two independent heuristics.
    """
    norm_path = path.replace("\\", "/")
    is_domain = "/domain/" in norm_path
    targets = []

    if is_domain:
        targets += [_ANTI_ANEMIC_OBJECT_CALLS_PORT, _RESULT_SHAPE]

    if "valueobjects" in norm_path or _PARSE_OR_HYDRATE_DEF_RE.search(fragments):
        targets.append(_PARSE_VS_HYDRATE)

    if _OK_CASE_RE.search(fragments) and _FEHLER_CASE_RE.search(fragments):
        targets.append(_RESULT_SHAPE)

    if not is_domain and _CALLER_PATTERN_MATCH_RE.search(fragments):
        targets.append(_ANTI_ANEMIC_OBJECT_CALLS_PORT)

    seen = set()
    result = []
    for t in targets:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result
