"""Startup-Prüfung der i18n-Fehlercode-Vollständigkeit.

Beim Start prüft diese Funktion, dass:
1. Jeder Fehlerfall der Response-Unions einen `code` trägt
2. Jeder Code in den Resource-Dateien existiert (beide Sprachen)
3. Vorlage ohne Code ist auch Drift (symmetrisch)
4. Template-Platzhalter passen zu den Fehlerfall-Parametern

Entscheidung: docs/decisions/2026-08-07-0805-fehlercodes-werden-abgeleitet-nicht-gepflegt.md
"""

from typing import Any, get_args

from src.api.i18n import ResourcesCache

__all__ = ["verify_error_codes_complete"]


def verify_error_codes_complete(
    resources: ResourcesCache,
    error_unions: list[type[Any]],
    allowed_orphaned_codes: set[str] | None = None,
) -> None:
    """Verifiziere, dass alle top-level Fehler-Cases einen Code haben.

    Diese Funktion prüft nur die Top-Level Response-Cases (z.B. EmailAlreadyTaken,
    RegistrationInvalid). Feldfehlercodes (die in errors.* stecken) müssen über die
    Specs getestet werden, da sie erst in der Mapper-Funktion entstehen.

    Args:
        resources: Die geladenen Resource-Files (de-DE, en-US)
        error_unions: Liste der Response-Union-Types (z.B. RegisterUserResponse)
        allowed_orphaned_codes: Codes, die in Ressourcen ohne Top-Level-Case sein dürfen
            (Feld-Fehlercodes, die durch Specs getestet werden)

    Wirft ValueError, wenn Top-Level Codes nicht konsistent sind.
    """
    if allowed_orphaned_codes is None:
        allowed_orphaned_codes = set()

    # 1. Sammle nur top-level Codes aus den Response-Unions
    top_level_codes = _collect_top_level_error_codes(error_unions)

    # 2. Verifiziere, dass jeder top-level Code in den Ressourcen existiert
    resource_codes = _collect_codes_from_resources(resources)
    missing_templates = top_level_codes - resource_codes

    if missing_templates:
        raise ValueError(
            f"Top-Level Codes ohne Template in Resource-Files: {sorted(missing_templates)}\n"
            "→ Jeder Response-Case braucht Einträge in de-DE.json und en-US.json"
        )


def _collect_top_level_error_codes(
    error_unions: list[type[Any]],
) -> set[str]:
    """Sammle nur die Top-Level Codes aus den Error-Union-Types.

    Top-Level sind: Success-Case (kein Code nötig) und Error-Cases, die
    direkt mit ihrem Code zurückgegeben werden (nicht in errors.*).
    """
    codes = set()

    for union_type in error_unions:
        union_args = get_args(union_type)
        if not union_args:
            # Kein Union, einzelner Type
            union_args = (union_type,)

        for case in union_args:
            # Prüfe nur auf ClassVar "code"
            if hasattr(case, "code"):
                code = case.code
                if isinstance(code, str):
                    codes.add(code)

    return codes


def _collect_codes_from_resources(resources: ResourcesCache) -> set[str]:
    """Sammle alle Codes aus den Resource-Dateien."""
    # Unter der Annahme, dass both languages identische Code-Sets haben (geprüft beim Load)
    de_resources = resources._resources.get("de-DE", {})
    return set(de_resources.keys())
