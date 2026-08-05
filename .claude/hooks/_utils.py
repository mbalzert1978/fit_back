#!/usr/bin/env python3
"""
Cross-platform utility functions for Claude Code hooks and scripts.
Works on Windows, macOS, and Linux.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from datetime import datetime
from pathlib import Path

# Platform detection
is_windows = sys.platform == "win32"
is_macos = sys.platform == "darwin"
is_linux = sys.platform.startswith("linux")

_SESSION_DATA_DIR_NAME = "session-data"
_LEGACY_SESSIONS_DIR_NAME = "sessions"
_WINDOWS_RESERVED_SESSION_IDS = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------

def get_home_dir() -> Path:
    explicit = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    if explicit and explicit.strip():
        return Path(explicit).resolve()
    return Path.home()


def get_claude_dir() -> Path:
    return get_home_dir() / ".claude"


def get_sessions_dir() -> Path:
    return get_claude_dir() / _SESSION_DATA_DIR_NAME


def get_legacy_sessions_dir() -> Path:
    return get_claude_dir() / _LEGACY_SESSIONS_DIR_NAME


def get_session_search_dirs() -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for d in (get_sessions_dir(), get_legacy_sessions_dir()):
        if d not in seen:
            seen.add(d)
            result.append(d)
    return result


def get_learned_skills_dir() -> Path:
    return get_claude_dir() / "skills" / "learned"


def get_temp_dir() -> Path:
    return Path(tempfile.gettempdir())


def ensure_dir(dir_path: Path | str) -> Path:
    p = Path(dir_path)
    try:
        p.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        pass
    return p


# ---------------------------------------------------------------------------
# Date / Time
# ---------------------------------------------------------------------------

def get_date_string() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_time_string() -> str:
    return datetime.now().strftime("%H:%M")


def get_datetime_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Session / Project
# ---------------------------------------------------------------------------

def sanitize_session_id(raw: str | None) -> str | None:
    if not raw or not isinstance(raw, str):
        return None

    has_non_ascii = any(ord(c) > 0x7F for c in raw)
    normalized = raw.lstrip(".")
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "-", normalized)
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")

    if sanitized:
        suffix = hashlib.sha256(normalized.encode()).hexdigest()[:6]
        if sanitized.upper() in _WINDOWS_RESERVED_SESSION_IDS:
            return f"{sanitized}-{suffix}"
        if has_non_ascii:
            return f"{sanitized}-{suffix}"
        return sanitized

    meaningful = re.sub(r"[\s\W]", "", normalized)
    if not meaningful:
        return None
    return hashlib.sha256(normalized.encode()).hexdigest()[:8]


def get_git_repo_name() -> str | None:
    result = run_command("git rev-parse --show-toplevel")
    if not result["success"]:
        return None
    return Path(result["output"]).name


def get_project_name() -> str | None:
    repo = get_git_repo_name()
    if repo:
        return repo
    name = Path.cwd().name
    return name or None


def get_session_id_short(fallback: str = "default") -> str:
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    if session_id:
        s = sanitize_session_id(session_id[-8:])
        if s:
            return s
    return sanitize_session_id(get_project_name()) or sanitize_session_id(fallback) or "default"


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------

def find_files(
    dir_path: Path | str,
    pattern: str,
    *,
    max_age: float | None = None,
    recursive: bool = False,
) -> list[dict]:
    """Return files matching a glob pattern, sorted newest-first.

    Each entry: {"path": Path, "mtime": float (epoch ms)}
    """
    dir_path = Path(dir_path)
    if not pattern or not dir_path.is_dir():
        return []

    regex_src = (
        re.escape(pattern)
        .replace(r"\*", ".*")
        .replace(r"\?", ".")
    )
    regex = re.compile(f"^{regex_src}$")
    results: list[dict] = []
    now_ms = datetime.now().timestamp() * 1000

    def _scan(current: Path) -> None:
        try:
            for entry in current.iterdir():
                if entry.is_file() and regex.match(entry.name):
                    try:
                        mtime_ms = entry.stat().st_mtime * 1000
                    except OSError:
                        continue
                    if max_age is None or (now_ms - mtime_ms) / 86_400_000 <= max_age:
                        results.append({"path": entry, "mtime": mtime_ms})
                elif entry.is_dir() and recursive:
                    _scan(entry)
        except PermissionError:
            pass

    _scan(dir_path)
    results.sort(key=lambda x: x["mtime"], reverse=True)
    return results


def read_file(file_path: Path | str) -> str | None:
    try:
        return Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return None


def write_file(file_path: Path | str, content: str) -> None:
    p = Path(file_path)
    ensure_dir(p.parent)
    p.write_text(content, encoding="utf-8")


def append_file(file_path: Path | str, content: str) -> None:
    p = Path(file_path)
    ensure_dir(p.parent)
    with p.open("a", encoding="utf-8") as f:
        f.write(content)


def replace_in_file(
    file_path: Path | str,
    search: str | re.Pattern,
    replace: str,
    *,
    all_occurrences: bool = False,
) -> bool:
    content = read_file(file_path)
    if content is None:
        return False
    try:
        if all_occurrences and isinstance(search, str):
            new_content = content.replace(search, replace)
        else:
            new_content = re.sub(search if isinstance(search, str) else search.pattern, replace, content)
        write_file(file_path, new_content)
        return True
    except Exception as e:
        log(f"[Utils] replace_in_file failed for {file_path}: {e}")
        return False


def count_in_file(file_path: Path | str, pattern: str | re.Pattern) -> int:
    content = read_file(file_path)
    if content is None:
        return 0
    try:
        if isinstance(pattern, re.Pattern):
            p = re.compile(pattern.pattern, pattern.flags)
        else:
            p = re.compile(pattern)
        return len(p.findall(content))
    except re.error:
        return 0


def grep_file(file_path: Path | str, pattern: str | re.Pattern) -> list[dict]:
    content = read_file(file_path)
    if content is None:
        return []
    try:
        if isinstance(pattern, re.Pattern):
            flags = pattern.flags & ~re.MULTILINE
            regex = re.compile(pattern.pattern, flags)
        else:
            regex = re.compile(pattern)
    except re.error:
        return []
    return [
        {"line_number": i + 1, "content": line}
        for i, line in enumerate(content.splitlines())
        if regex.search(line)
    ]


# ---------------------------------------------------------------------------
# String utilities
# ---------------------------------------------------------------------------

_ANSI_ESCAPE = re.compile(
    r"\x1b(?:\[[0-9;?]*[A-Za-z]|\][^\x07\x1b]*(?:\x07|\x1b\\)|\([A-Z]|[A-Z])"
)


def strip_ansi(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return _ANSI_ESCAPE.sub("", s)


# ---------------------------------------------------------------------------
# Hook I/O
# ---------------------------------------------------------------------------

def read_stdin_json(timeout_ms: int = 5000) -> dict:
    """Read JSON from stdin with a timeout. Returns {} on failure."""
    result: list[dict] = [{}]

    def _read() -> None:
        try:
            data = sys.stdin.read()
            if data.strip():
                result[0] = json.loads(data)
        except Exception:
            pass

    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout=timeout_ms / 1000)
    return result[0]


def log(message: str) -> None:
    print(message, file=sys.stderr)


def output(data: dict | str) -> None:
    if isinstance(data, dict):
        print(json.dumps(data))
    else:
        print(data)


# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------

def command_exists(cmd: str) -> bool:
    if not re.match(r"^[a-zA-Z0-9_.-]+$", cmd):
        return False
    return shutil.which(cmd) is not None


_ALLOWED_COMMAND_PREFIXES = ("git ", "python ", "python3 ", "dotnet ", "which ", "where ")
_SHELL_METACHAR_RE = re.compile(r"[;|&\n`$]")


def run_command(cmd: str, **kwargs) -> dict:
    """Run a shell command and return {"success": bool, "output": str}.

    Only permits commands starting with a known-safe prefix.
    Rejects shell metacharacters to prevent injection.
    """
    if not any(cmd.startswith(p) for p in _ALLOWED_COMMAND_PREFIXES):
        return {"success": False, "output": "run_command blocked: unrecognized command prefix"}
    unquoted = re.sub(r'"[^"]*"', "", re.sub(r"'[^']*'", "", cmd))
    if _SHELL_METACHAR_RE.search(unquoted):
        return {"success": False, "output": "run_command blocked: shell metacharacters not allowed"}
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            **kwargs,
        )
        success = proc.returncode == 0
        return {"success": success, "output": (proc.stdout or proc.stderr or "").strip()}
    except Exception as e:
        return {"success": False, "output": str(e)}


def is_git_repo() -> bool:
    return run_command("git rev-parse --git-dir")["success"]


def get_git_modified_files(patterns: list[str] | None = None) -> list[str]:
    if not is_git_repo():
        return []
    result = run_command("git diff --name-only HEAD")
    if not result["success"]:
        return []
    files = [f for f in result["output"].splitlines() if f]
    if not patterns:
        return files
    compiled: list[re.Pattern] = []
    for p in patterns:
        if isinstance(p, str) and p:
            try:
                compiled.append(re.compile(p))
            except re.error:
                pass
    if not compiled:
        return files
    return [f for f in files if any(rx.search(f) for rx in compiled)]
