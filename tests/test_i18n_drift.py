"""Die Drift-Pruefung: schlaegt sie an, wenn Fehlerfaelle und Vorlagen auseinanderlaufen?

Der erste Test ist der eigentliche Nutzen - er faehrt dieselbe Aufzaehlung wie der
Zusammenbau und faellt in CI aus, bevor jemand deployt. Die uebrigen belegen, dass die
Pruefung nicht bloss immer gruen meldet: zu jeder Abweichung, die sie fangen soll, gibt es
einen Fall, in dem sie nachweislich anschlaegt.
"""

from dataclasses import dataclass
from typing import ClassVar, final

import pytest

from src.api.i18n import create_resources
from src.api.i18n_startup_check import verify_error_codes_complete
from src.main import ERROR_UNIONS, PRESENTATION_CODES


@final
class FakeResources:
    """Sprachdateien aus dem Speicher - dieselbe Naht wie `ResourcesCache`."""

    def __init__(self, templates: dict[str, str]) -> None:
        self._templates = templates

    @property
    def languages(self) -> frozenset[str]:
        return frozenset({"de-DE"})

    def codes(self, language: str) -> frozenset[str]:
        return frozenset(self._templates) if language == "de-DE" else frozenset()

    def get(self, language: str, code: str) -> str | None:
        return self._templates.get(code) if language == "de-DE" else None


@final
@dataclass(frozen=True, slots=True)
class ThingTooLong:
    code: ClassVar[str] = "thing-too-long"
    maximum: int


@final
@dataclass(frozen=True, slots=True)
class ThingIsEmpty:
    code: ClassVar[str] = "thing-is-empty"


@final
@dataclass(frozen=True, slots=True)
class Uncoded:
    """Ein Fall, dessen Autor den Code vergessen hat."""


type ThingError = ThingTooLong | ThingIsEmpty


def test_der_zusammenbau_ist_driftfrei() -> None:
    """Die echten Unions und die echten Sprachdateien passen zusammen.

    Faellt dieser Test aus, bringt ein Slice Fehlerfaelle mit, deren Texte fehlen - oder
    in den Sprachdateien liegen Vorlagen, zu denen es keinen Fall mehr gibt.
    """
    verify_error_codes_complete(create_resources(), ERROR_UNIONS, PRESENTATION_CODES)


def test_ein_code_ohne_vorlage_faellt_auf() -> None:
    resources = FakeResources({"thing-too-long": "hoechstens {maximum}"})

    with pytest.raises(ValueError, match="keine Vorlage") as caught:
        verify_error_codes_complete(resources, [ThingError])

    assert "thing-is-empty" in str(caught.value)


def test_eine_vorlage_ohne_fall_faellt_auf() -> None:
    """Karteileichen sind die andere Haelfte des Drifts."""
    resources = FakeResources(
        {
            "thing-too-long": "hoechstens {maximum}",
            "thing-is-empty": "leer",
            "thing-vergessen": "zu einem Fall, den es nicht mehr gibt",
        }
    )

    with pytest.raises(ValueError, match="ohne Fehlerfall") as caught:
        verify_error_codes_complete(resources, [ThingError])

    assert "thing-vergessen" in str(caught.value)


def test_ein_platzhalter_ohne_nutzlast_faellt_auf() -> None:
    """Sonst schluege das Rendern erst zu, wenn jemand den Fehler ausloest."""
    resources = FakeResources(
        {
            "thing-too-long": "hoechstens {maximum} von {gibt_es_nicht}",
            "thing-is-empty": "leer",
        }
    )

    with pytest.raises(ValueError, match="Vorlage verlangt") as caught:
        verify_error_codes_complete(resources, [ThingError])

    assert "gibt_es_nicht" in str(caught.value)


def test_ein_fall_ohne_code_faellt_auf() -> None:
    with pytest.raises(ValueError, match="ohne `code`") as caught:
        verify_error_codes_complete(FakeResources({}), [Uncoded])

    assert "Uncoded" in str(caught.value)


def test_zwei_faelle_mit_demselben_code_fallen_auf() -> None:
    """Ein Code gehoert genau einem Fall - sonst ist unklar, wessen Nutzlast gilt."""

    @final
    @dataclass(frozen=True, slots=True)
    class Doppelgaenger:
        code: ClassVar[str] = ThingIsEmpty.code

    with pytest.raises(ValueError, match="doppelt vergeben"):
        verify_error_codes_complete(FakeResources({}), [ThingError, Doppelgaenger])
