"""Drift-Prüfung beim Start — Konsistenz zwischen Fehlerfällen und Textvorlagen.

Die erwartete Code-Menge wird **aus den Fehler-Unions abgeleitet**, nicht danebengepflegt.
Damit kann ein neuer Slice keine Fehlerfaelle mitbringen, deren Texte niemand hinterlegt
hat: sobald seine Union im Zusammenbau auftaucht, sind ihre Codes Teil der Erwartung, und
eine fehlende Vorlage laesst die Anwendung beim Start scheitern statt erst beim Nutzer.

Geprueft wird in beide Richtungen und auf drei Ebenen:

1. Jeder Fall jeder uebergebenen Union traegt einen `code` (`CodedError`).
2. Zu jedem Code gibt es in **jeder** Sprache eine Vorlage, und zu jeder Vorlage einen
   Code. Karteileichen sind die andere Haelfte des Drifts.
3. Die Platzhalter einer Vorlage kommen in der Nutzlast ihres Falls vor. Sonst schluege
   das Rendern erst zu, wenn jemand den Fehler ausloest.

Entscheidung: docs/decisions/2026-08-07-0805-fehlercodes-werden-abgeleitet-nicht-gepflegt.md
"""

from collections.abc import Iterable
from string import Formatter
from typing import Protocol

from src.contexts.shared_kernel.coded_error import codes_of, parameters_of

__all__ = ["ErrorTemplates", "verify_error_codes_complete"]


class ErrorTemplates(Protocol):
    """Die drei Zugriffe, die diese Pruefung auf den Sprachdateien braucht.

    Ein Vertrag statt der konkreten `ResourcesCache`: die ist `@final`, ein
    Test-Doppel koennte sie sonst weder erben noch erfuellen.
    """

    @property
    def languages(self) -> frozenset[str]:
        """Nenne die geladenen Sprachen."""
        ...

    def codes(self, language: str, /) -> frozenset[str]:
        """Nenne die Codes, zu denen in dieser Sprache eine Vorlage vorliegt."""
        ...

    def get(self, language: str, code: str, /) -> str | None:
        """Hole die Vorlage - `None`, wenn die Sprache oder der Code fehlt."""
        ...


def verify_error_codes_complete(
    resources: ErrorTemplates,
    error_unions: Iterable[object],
    presentation_codes: frozenset[str] = frozenset(),
) -> None:
    """Vergleiche die Fehlerfaelle der Unions mit den hinterlegten Vorlagen.

    Args:
        resources: die geladenen Sprachdateien.
        error_unions: die Fehler-Unions aller zusammengebauten Slices. Der Zusammenbau
            ist die einzige Stelle, die sie alle kennt - deshalb reicht er sie herein,
            statt dass dieses Modul sie sich per Import-Seiteneffekt zusammensucht (ein
            nicht importierter Slice fehlte dort still).
        presentation_codes: Codes, die am HTTP-Rand entstehen und zu keinem
            Domaenen-Fehlerfall gehoeren (`validation-failed`, die `-detail`-Haelften,
            die Idempotency-Meldungen). Sie werden auf Vorhandensein geprueft, aber nicht
            auf Platzhalter - ihre Nutzlast ist nicht typisiert. **Uebergangsloesung:**
            sobald der Rand seine strukturellen Fehler als eigene Tagged Union fuehrt,
            wandern sie nach `error_unions` und dieser Parameter entfaellt.

    Raises:
        ValueError: sobald eine der drei Ebenen nicht aufgeht - mit allen Abweichungen
            auf einmal, nicht nur der ersten. Wer eine Sprachdatei ergaenzt, will nicht
            beim naechsten Start die naechste Meldung sehen.

    """
    by_code = codes_of(*error_unions)  # Ebene 1: wirft, wenn ein Fall keinen Code traegt
    expected = set(by_code) | set(presentation_codes)

    if problems := [
        *_missing_and_orphaned(resources, expected),
        *_placeholder_mismatches(resources, by_code),
    ]:
        listing = "\n  - ".join(problems)
        msg = f"i18n-Drift zwischen Fehlerfaellen und Resource-Files:\n  - {listing}"
        raise ValueError(msg)


def _missing_and_orphaned(resources: ErrorTemplates, expected: set[str]) -> list[str]:
    """Ebene 2: fehlende Vorlagen je Sprache, und Vorlagen ohne Fall."""
    problems = []
    for language in sorted(resources.languages):
        available = resources.codes(language)
        if missing := sorted(expected - available):
            problems.append(f"{language}: keine Vorlage fuer {missing}")
        if orphaned := sorted(available - expected):
            problems.append(f"{language}: Vorlage ohne Fehlerfall fuer {orphaned}")
    return problems


def _placeholder_mismatches(resources: ErrorTemplates, by_code: dict[str, type]) -> list[str]:
    """Ebene 3: Platzhalter, die die Nutzlast ihres Falls nicht hergibt."""
    problems = []
    for language in sorted(resources.languages):
        for code, case in sorted(by_code.items()):
            template = resources.get(language, code)
            if template is None:
                continue  # schon als fehlend gemeldet
            payload = parameters_of(case)
            if unknown := sorted(_placeholders(template) - payload):
                problems.append(
                    f"{language}/{code}: Vorlage verlangt {unknown}, "
                    f"{case.__name__} traegt {sorted(payload)}"
                )
    return problems


def _placeholders(template: str) -> set[str]:
    """Lies die benannten Platzhalter einer Vorlage."""
    return {name for _, name, _, _ in Formatter().parse(template) if name}
