#!/usr/bin/env python3
# SessionStart/PreCompact/SessionEnd hook: outputs context-aware reminders about session state.
# Sessions are individual files in docs/sessions/ (YYYY-MM-DD-HHMM-<slug>.md).
# Never writes files. Exit 0 always (observer only).
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import load_hook_input

data = load_hook_input()

event = data.get("hook_event_name", "Unknown")
project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
sessions_dir = project_dir / "docs" / "sessions"

print(f"=== session-state-handler ({event}) ===")


def find_latest_session():
    if not sessions_dir.is_dir():
        return None
    files = sorted(sessions_dir.glob("*.md"))
    return files[-1] if files else None


def git_status():
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "  (kein Git-Repo oder git nicht verfügbar)"


def git_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip().replace("/", "-") if result.returncode == 0 else "unknown"


if event == "SessionStart":
    latest = find_latest_session()
    if latest:
        rel = latest.relative_to(project_dir)
        print(f"Bitte {rel} zuerst lesen:")
        print("  - Letzten Eintrag mit aktueller Repo-Realität abgleichen")
        print("  - Offene 'Next Steps' übernehmen")
        print("  - Diskrepanzen flaggen, bevor neue Arbeit beginnt")
    else:
        print("WARN: Keine Session-Dateien in docs/sessions/ gefunden.")
    print()
    print("Aktueller git-Status:")
    status = git_status()
    print(status if status else "  (keine Änderungen)")

elif event == "PreCompact":
    print("Kontext wird gleich kompaktiert. Vorher in docs/sessions/ festhalten:")
    print("  - Wichtige Entscheidungen dieser Session (mit Begründung)")
    print("  - Aktuell uncommitted Changes (file paths)")
    print("  - Was als Nächstes zu tun ist, falls die Session jetzt enden würde")

elif event == "SessionEnd":
    branch = git_branch()
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    suggested = f"docs/sessions/{timestamp}-{branch}.md"
    print("Session schließt. Neue Session-Datei anlegen:")
    print(f"  Pfad: {suggested}")
    print()
    print("  Format (Caveman-Stil, Deutsch, kein Füllwort):")
    print("  ---")
    print(f"  name: {timestamp}-{branch}")
    print("  description: >")
    print("    Einzeiler: was Session erreicht hat")
    print("  ---")
    print()
    print(f"  **Branch:** `{branch}`")
    print()
    print("  ## Was wurde getan")
    print("  - <Aktion>. <Ergebnis>.")
    print()
    print("  ## Entscheidungen")
    print("  - <Entscheidung> -> <Grund>.")
    print()
    print("  ## Uncommitted Changes")
    print("  keine  (oder Dateiliste)")
    print()
    print("  ## Next Steps")
    print("  - <Task>: <Was genau> -> <Ergebnis>")
    print()
    print("Offene Commits prüfen:")
    status = git_status()
    print(status if status else "  (keine Änderungen)")

else:
    print("Hinweis: unbekanntes Hook-Event — keine spezifische Aktion.")

sys.exit(0)
