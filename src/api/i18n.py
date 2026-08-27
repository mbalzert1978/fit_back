"""i18n support für HTTP-Rand: Resource-Files, Accept-Language-Auswertung, Rendering.

Die Sprache wird allein nach `Accept-Language` entschieden (nicht nach User.locale),
um zu vermeiden, dass jeder Fehlerfall am Rand einen Datenbankzugriff kostet.

Alle Resource-Dateien werden beim Start der Applikation geladen und auf
Vollständigkeit geprüft - fehlt ein Code in einer Datei, ist das ein Startfehler
(raises TypeError für malformed JSON, ValueError für fehlende Codes), kein Laufzeitfehler.
"""

import contextlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import final

from fastapi import Request

__all__ = [
    "ResourcesCache",
    "create_resources",
    "get_language_from_header",
    "language_of",
    "resources_of",
    "translate",
]

SUPPORTED_LANGUAGES = {"de-DE", "en-US"}
DEFAULT_LANGUAGE = "de-DE"

# Fallback auf Sprache (de-AT -> de-DE, en-GB -> en-US)
LANGUAGE_FALLBACKS: Mapping[str, str] = {
    "de": "de-DE",
    "en": "en-US",
}


@final
class ResourcesCache:
    """Lade Resource-Dateien einmalig und halte sie im Speicher."""

    def __init__(self) -> None:
        """Initialisiere die Ressourcen beim Laden."""
        self._resources: dict[str, dict[str, str]] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Lade alle unterstützten Sprachen und prüfe auf Vollständigkeit."""
        all_codes: set[str] = set()

        # Erste Pass: alle Codes sammeln
        for language in SUPPORTED_LANGUAGES:
            path = Path(__file__).parent / "resources" / f"{language}.json"
            with path.open("r", encoding="utf-8") as f:
                content = json.load(f)
            if not isinstance(content, dict):
                msg = f"Resource file {path} must contain a JSON object"
                raise TypeError(msg)
            self._resources[language] = content
            all_codes.update(content.keys())

        # Zweite Pass: auf Vollständigkeit prüfen
        for language in SUPPORTED_LANGUAGES:
            if missing := all_codes - self._resources[language].keys():
                msg = f"Language '{language}' is missing codes: {sorted(missing)}"
                raise ValueError(msg)

    @property
    def languages(self) -> frozenset[str]:
        """Nenne die geladenen Sprachen."""
        return frozenset(self._resources)

    def codes(self, language: str) -> frozenset[str]:
        """Nenne die Codes, zu denen in dieser Sprache eine Vorlage vorliegt."""
        return frozenset(self._resources.get(language, {}))

    def get(self, language: str, code: str) -> str | None:
        """Hole die Vorlage für einen Code in einer Sprache."""
        if language not in self._resources:
            return None
        return self._resources[language].get(code)

    def translate(self, code: str, parameters: Mapping[str, object], language: str) -> str:
        """Übersetze einen Code + Parameter zu Text."""
        template = self.get(language, code)
        if template is None:
            template = self.get(DEFAULT_LANGUAGE, code)
        if template is None:
            # Sollte nie vorkommen, da beim Start geprüft
            msg = f"Code '{code}' not found in any language"
            raise AssertionError(msg)

        try:
            return template.format(**parameters)
        except KeyError as e:
            msg = f"Template for '{code}' references unknown parameter {e.args[0]!r}"
            raise AssertionError(msg) from e


def create_resources() -> ResourcesCache:
    """Erstelle und validiere die Resource-Dateien beim Startup.

    Wirft TypeError für malformed JSON, ValueError für fehlende Codes.
    """
    return ResourcesCache()


def translate(
    resources: ResourcesCache,
    code: str,
    parameters: Mapping[str, object] | None = None,
    language: str | None = None,
) -> str:
    """Übersetze einen Code + Parameter zu Text in einer Sprache.

    Args:
        resources: Die geladenen Sprachdateien.
        code: Der zu übersetzende Fehlercode (aus Fehler-Union, beim Start gegen
            Ressourcen geprüft)
        parameters: Optional dict mit Parametern für Template-Platzhalter
        language: Zielsprache (de-DE oder en-US). Default: de-DE. In HTTP-Kontext IMMER explizit
            von Accept-Language-Header übergeben; None-Default ist nur für Tests/Logging sinnvoll.

    Wirft AssertionError, wenn der Code nicht existiert oder Parameter fehlen — das ist ein
    Programmierfehler und beruht auf fehlgeschlagener Startup-Prüfung der Drift-Abgleiche.

    """
    if parameters is None:
        parameters = {}
    if language is None:
        language = DEFAULT_LANGUAGE
    return resources.translate(code, parameters, language)


def _quality_of(parameters: str) -> float:
    """Lies das q-Gewicht aus den Parametern eines Language-Range.

    Ein fehlendes oder defektes q (q=abc) lässt das Defaultgewicht 1.0 stehen;
    Werte außerhalb [0, 1] werden auf den Bereich beschnitten.
    """
    for parameter in parameters.split(";"):
        stripped = parameter.strip()
        if stripped.startswith("q="):
            with contextlib.suppress(ValueError):
                return max(0.0, min(1.0, float(stripped[2:])))
    return 1.0


def _range_of(part: str) -> tuple[str, float] | None:
    """Zerlege einen Header-Eintrag ("de-AT;q=0.9") in Tag und Gewicht.

    Leere Einträge und der Wildcard `*` sind keine Sprachwahl und fallen weg.
    """
    tag, _, parameters = part.strip().partition(";")
    tag = tag.strip()
    return None if not tag or tag == "*" else (tag, _quality_of(parameters))


def _supported_form_of(tag: str) -> str | None:
    """Bilde ein Language-Tag auf eine unterstützte Sprache ab, sonst None.

    Erst die exakte Übereinstimmung (auf BCP 47 normalisiert, de_DE ⇒ de-DE,
    Groß-/Kleinschreibung egal), dann der reine Sprachtreffer (de-AT ⇒ de-DE).
    """
    normalized = tag.replace("_", "-").lower()
    exact = next(
        (language for language in SUPPORTED_LANGUAGES if language.lower() == normalized), None
    )
    return exact or LANGUAGE_FALLBACKS.get(normalized.split("-")[0])


def get_language_from_header(accept_language: str | None) -> str:
    """Parse den Accept-Language-Header und wähle die beste passende Sprache.

    Regeln (RFC 7231):
    - q-Gewichte werden ausgewertet, höchstes gewinnt
    - Bei Gleichstand die zuerst genannte Sprache
    - Ein reiner Regionstreffer zählt (de-AT ⇒ de-DE, en-GB ⇒ en-US)
    - Defekte q-Werte (z.B. q=abc) werden ignoriert, die Sprache behält Defaultgewicht 1.0
    - Unbekannte Sprache, q=0, leerer oder syntaktisch defekter Header ⇒ de-DE
    - Die Sprachwahl darf nie eine sonst gültige Anfrage scheitern lassen

    Returns:
        Ein unterstütztes Sprach-Tag oder DEFAULT_LANGUAGE.

    """
    ranges = [entry for entry in map(_range_of, (accept_language or "").split(",")) if entry]
    # sorted ist stabil, das erhält bei gleichem Gewicht die Reihenfolge des Headers
    by_quality = sorted(ranges, key=lambda entry: -entry[1])
    return next(
        (
            supported
            for tag, quality in by_quality
            # q=0 heißt "akzeptiere ich nicht"
            if quality > 0 and (supported := _supported_form_of(tag))
        ),
        DEFAULT_LANGUAGE,
    )


def language_of(request: Request) -> str:
    """Die ausgehandelte Sprache dieser Anfrage.

    Die eine Stelle, an der `Accept-Language` ausgewertet wird. Ohne
    Zwischenspeicher - mehrfach gefragt kommt mehrfach dasselbe heraus.
    """
    return get_language_from_header(request.headers.get("accept-language"))


def resources_of(request: Request) -> ResourcesCache:
    """Die beim Start geladenen Ressourcen dieser Anwendung.

    Vorbedingung: der Lifespan in `src/main.py` hat sie in `app.state.resources`
    abgelegt. Fehlen sie, bricht der Aufruf **hier** ab statt weiter unten in
    `translate`.
    """
    resources: ResourcesCache | None = getattr(request.app.state, "resources", None)
    if resources is None:
        msg = (
            "app.state.resources fehlt - die App lief ohne ihren Lifespan. Der Lifespan in "
            "src/main.py legt sie ueber create_resources() an; ein Test, der seine App selbst "
            "baut, setzt app.state.resources = create_resources()."
        )
        raise AssertionError(msg)
    return resources
