#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""Prueft die Voraussetzungen der Claude-Seite dieses Repos.

Aufruf ueber `./make.ps1 claude-doctor`, `uv run scripts/claude_doctor.py` oder direkt.
Ein Befund ist ein eigener Fall, kein Satz: was gefunden wurde, steht im Typ, nicht im Text.
Exit 1, sobald ein Befund existiert, sonst 0.
"""

import json
import re
import shutil
import sys
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Final, assert_never, final

REPO: Final = Path(__file__).resolve().parent.parent
TOOLS: Final = ("uv", "gh", "semble")
SETTINGS: Final = (".claude/settings.json", ".claude/settings.local.json")

# ponytail: ein Hook-Kommando ist eine Shell-Zeile; pruefenswert ist daran nur der
# Skriptpfad, auf den sie zeigt - alles zwischen $CLAUDE_PROJECT_DIR/ und dem
# schliessenden Anfuehrungszeichen.
HOOK_PATH: Final = re.compile(r"\$CLAUDE_PROJECT_DIR/([^\"']+)")


@final
@dataclass(frozen=True, slots=True)
class MissingTool:
    """Ein erwartetes Werkzeug liegt nicht im PATH."""

    tool: str


@final
@dataclass(frozen=True, slots=True)
class MissingSettings:
    """Eine Settings-Datei, die es geben muss, existiert nicht."""

    settings: str


@final
@dataclass(frozen=True, slots=True)
class UnreadableSettings:
    """Eine Settings-Datei existiert, laesst sich aber nicht als JSON lesen."""

    settings: str
    reason: str


@final
@dataclass(frozen=True, slots=True)
class DanglingHook:
    """Ein Hook-Kommando zeigt auf eine Datei, die es nicht gibt."""

    settings: str
    referenced: str


type Finding = MissingTool | MissingSettings | UnreadableSettings | DanglingHook


def render(finding: Finding) -> str:
    """Uebersetzt einen Befund in seine Ausgabezeile."""
    match finding:
        case MissingTool(tool):
            return f"Werkzeug nicht im PATH: {tool}"
        case MissingSettings(settings):
            return f"Settings-Datei fehlt: {settings}"
        case UnreadableSettings(settings, reason):
            return f"Settings-Datei nicht lesbar: {settings} ({reason})"
        case DanglingHook(settings, referenced):
            return f"{settings}: Hook zeigt auf fehlende Datei: {referenced}"
        case unreachable:
            assert_never(unreachable)


def _hook_references(hook: object) -> tuple[str, ...]:
    """Ein einzelner Hook: nur ein Kommando traegt Pfade, alles andere faellt raus."""
    match hook:
        case {"type": "command", "command": str(command)}:
            return tuple(HOOK_PATH.findall(command))
        case _:
            return ()


def _matcher_references(matcher: object) -> tuple[str, ...]:
    """Ein Matcher-Eintrag traegt seine Hooks unter `hooks`."""
    match matcher:
        case {"hooks": [*hooks]}:
            return tuple(chain.from_iterable(map(_hook_references, hooks)))
        case _:
            return ()


def _event_references(matchers: object) -> tuple[str, ...]:
    """Ein Event (`PreToolUse` &c.) traegt eine Liste von Matcher-Eintraegen."""
    match matchers:
        case [*entries]:
            return tuple(chain.from_iterable(map(_matcher_references, entries)))
        case _:
            return ()


def hook_references(document: object) -> tuple[str, ...]:
    """Liest die Skriptpfade aller `type: command`-Hooks aus einem rohen Settings-Dokument.

    Die einzige Stelle, an der ungetyptes JSON vorkommt. Jede Ebene ist ein `match` auf die
    Struktur, die sie erwartet; was nicht passt, traegt keine Pfade und faellt lautlos raus.
    """
    match document:
        case {"hooks": {**events}}:
            return tuple(chain.from_iterable(map(_event_references, events.values())))
        case _:
            return ()


def inspect_tools(tools: tuple[str, ...]) -> tuple[Finding, ...]:
    """Sucht jedes Werkzeug im PATH."""
    return tuple(MissingTool(tool) for tool in tools if shutil.which(tool) is None)


def inspect_settings(repo: Path, settings: str) -> tuple[Finding, ...]:
    """Liest eine Settings-Datei und prueft die Ziele ihrer Hook-Kommandos."""
    path = repo / settings
    if not path.is_file():
        return (MissingSettings(settings),)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:  # die IO-Naht, sonst nirgends
        return (UnreadableSettings(settings, str(exc)),)
    return tuple(
        DanglingHook(settings, referenced)
        for referenced in hook_references(document)
        if not (repo / referenced).is_file()
    )


def inspect(repo: Path) -> tuple[Finding, ...]:
    """Alle Befunde in Ausgabereihenfolge; leer heisst: nichts zu melden."""
    return inspect_tools(TOOLS) + tuple(
        chain.from_iterable(inspect_settings(repo, settings) for settings in SETTINGS)
    )


def main() -> int:
    """Gibt die Befunde aus und liefert den Exit-Code."""
    findings = inspect(REPO)
    for finding in findings:
        print(f"FAIL  {render(finding)}")
    if findings:
        return 1
    print(f"OK    {', '.join(TOOLS)} im PATH, Hook-Referenzen aufloesbar")
    return 0


def demo() -> None:
    """Selbsttest: `uv run scripts/claude_doctor.py --demo`."""
    hooks = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {"type": "command", "command": 'uv run "$CLAUDE_PROJECT_DIR/a.py"'},
                        {"type": "prompt", "prompt": "kein Kommando"},
                    ],
                }
            ]
        }
    }
    assert hook_references(hooks) == ("a.py",)
    for junk in ({}, "kein Dokument", 42, None, {"hooks": []}, {"hooks": {"X": [{"hooks": 1}]}}):
        assert hook_references(junk) == (), junk
    assert inspect_tools(("gibt-es-nicht",)) == (MissingTool("gibt-es-nicht"),)
    assert inspect_settings(Path("/nirgendwo"), "x.json") == (MissingSettings("x.json"),)
    assert render(DanglingHook("s.json", "h.py")) == "s.json: Hook zeigt auf fehlende Datei: h.py"
    print("demo ok")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        raise SystemExit(main())
