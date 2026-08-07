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

__all__ = ["ResourcesCache", "create_resources", "get_language_from_header", "translate"]

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
                raise TypeError(f"Resource file {path} must contain a JSON object")
            self._resources[language] = content
            all_codes.update(content.keys())

        # Zweite Pass: auf Vollständigkeit prüfen
        for language in SUPPORTED_LANGUAGES:
            if missing := all_codes - self._resources[language].keys():
                raise ValueError(f"Language '{language}' is missing codes: {sorted(missing)}")

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
            # Fallback auf Default-Sprache
            template = self.get(DEFAULT_LANGUAGE, code)
        if template is None:
            # Sollte nie vorkommen, da beim Start geprüft
            raise AssertionError(f"Code '{code}' not found in any language")

        # Benannte Platzhalter aus Parametern ausfüllen
        try:
            return template.format(**parameters)
        except KeyError as e:
            raise AssertionError(
                f"Template for '{code}' references unknown parameter {e.args[0]!r}"
            ) from e


def create_resources() -> ResourcesCache:
    """Erstelle und validiere die Resource-Dateien beim Startup.

    Diese Funktion wird von der Anwendung während der Initialisierung
    aufgerufen, um sicherzustellen, dass alle Fehlercodes in allen Sprachen
    definiert sind. Die Instanz wird in app.state.resources gespeichert.
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
        resources: Die ResourcesCache-Instanz (aus request.app.state.resources, garantiert im Lifespan)
        code: Der zu übersetzende Fehlercode (aus Fehler-Union, beim Start gegen Ressourcen geprüft)
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
    if not accept_language or not accept_language.strip():
        return DEFAULT_LANGUAGE

    # Parse alle Sprachen mit ihren q-Gewichten
    languages_with_quality: list[tuple[str, float, int]] = []

    for i, part in enumerate(accept_language.split(",")):
        part = part.strip()
        if not part:
            continue

        # Splitze in Sprache und Parameter (z.B. "de;q=0.9")
        quality = 1.0
        if ";" in part:
            lang_part, params_part = part.split(";", 1)
            lang = lang_part.strip()

            # Parse q-Gewicht — defekte q-Werte werden mit Defaultgewicht ignoriert
            for param in params_part.split(";"):
                param = param.strip()
                if param.startswith("q="):
                    with contextlib.suppress(ValueError):
                        quality = float(param[2:])
                        # Begrenze auf [0, 1]
                        quality = max(0.0, min(1.0, quality))
        else:
            lang = part.strip()

        if lang and lang != "*":
            # Speichere auch den Index für Gleichstand-Auflösung
            languages_with_quality.append((lang, quality, i))

    # Sortiere nach q-Gewicht (absteigend), dann nach Index (aufsteigend)
    languages_with_quality.sort(key=lambda x: (-x[1], x[2]))

    # Wähle die beste Sprache
    for lang_tag, quality, _ in languages_with_quality:
        if quality == 0:
            # q=0 bedeutet "akzeptiere ich nicht"
            continue

        # Normalisiere auf BCP 47 (de-DE, nicht DE-DE)
        lang_tag_normalized = lang_tag.replace("_", "-").lower()

        # 1. Exakte Übereinstimmung (case-insensitive)?
        for supported_lang in SUPPORTED_LANGUAGES:
            if supported_lang.lower() == lang_tag_normalized:
                return supported_lang

        # 2. Regionstreffer? (de → de-DE, en → en-US)
        lang_only = lang_tag_normalized.split("-")[0]
        if lang_only in LANGUAGE_FALLBACKS:
            return LANGUAGE_FALLBACKS[lang_only]

    # Keine passende Sprache gefunden → Default
    return DEFAULT_LANGUAGE
