"""Die veroeffentlichte Fehler-Vokabel des Identity-Context.

Ein Fehlercode ist der sprachunabhaengige Teil des API-Vertrags - `title` und `detail`
sind Kosmetik darueber. Dieser Test haelt fest, was dieser Context nach aussen zusagt, und
zwar an den drei Stellen, an denen es sonst still kaputtgehen wuerde:

1. Jeder veroeffentlichte Fall traegt einen Code, und keine zwei Faelle teilen sich einen.
2. Ueber die Naht wandern nur Primitive - ein Fall mit einem Value Object in der Nutzlast
   wuerde ein Domaenenobjekt nach draussen reichen.
3. Die bewusst **unveroeffentlichten** Faelle tragen weiterhin keinen Code. Das ist eine
   Entscheidung, die man einer Datei nicht ansieht: wer sie fuer ein Versehen haelt und
   "nachbessert", verlangt damit Textvorlagen fuer Faelle, die nie ein Nutzer sieht.

Was darueber hinaus zwischen Faellen und Sprachdateien abgeglichen wird, prueft
`tests/test_i18n_drift.py` - hier geht es nur um die Vokabel dieses Context.
"""

from dataclasses import fields, is_dataclass
from typing import get_args, get_type_hints

import pytest

from src.contexts.identity.domain import (
    DisplayNameError,
    DomainError,
    EmailAlreadyRegistered,
    EmailError,
    LocaleError,
    PasswordError,
    PasswordHashError,
    UserIdError,
    UserTimeZoneError,
)
from src.contexts.shared_kernel.coded_error import codes_of, error_cases, parameters_of

# Die Feldfehler-Unions, deren Codes in `errors.*` landen. Bewusst hier aufgezaehlt und
# nicht aus `src.main` importiert: dort steht die Aufzaehlung **aller** Slices, dieser
# Test spricht nur fuer Identity.
PUBLISHED = [EmailError, PasswordError, DisplayNameError, LocaleError, UserTimeZoneError]

# Faelle, die den Rand nie erreichen: sie stammen aus dem Hasher und aus
# `UserId.generate()`, nicht aus der Anfrage - ein Code wuerde eine Textvorlage
# einfordern, die niemand liest.
INTERNAL_ONLY = [UserIdError, PasswordHashError]

# Eigener Ausgang mit eigenem Statuscode, kein Feldfehler. Traegt selbst keinen Code:
# veroeffentlicht wird `EmailAlreadyTaken`, und ein Code gehoert laut
# `shared_kernel/coded_error.py` genau einmal an genau einen Fall.
KOLLISION = [EmailAlreadyRegistered]

_ALLOWED_SCALARS = (str, int, float, bool)


def _leaf_types(annotation: object) -> list[object]:
    """Zerlege eine Annotation bis auf ihre Blaetter (`tuple[str, ...]` -> `str`)."""
    if not (args := get_args(annotation)):
        return [annotation]
    return [leaf for arg in args if arg is not Ellipsis for leaf in _leaf_types(arg)]


@pytest.mark.parametrize("case", error_cases(*PUBLISHED), ids=lambda case: case.__name__)
def test_jeder_veroeffentlichte_fall_traegt_einen_code(case: type) -> None:
    code = getattr(case, "code", None)

    assert isinstance(code, str)
    assert code, f"{case.__name__} traegt einen leeren Code"


def test_kein_code_ist_doppelt_vergeben() -> None:
    """`codes_of` wirft bei Dopplung - ein Code gehoert genau einem Fall."""
    assert len(codes_of(*PUBLISHED)) == len(error_cases(*PUBLISHED))


@pytest.mark.parametrize("case", error_cases(*PUBLISHED), ids=lambda case: case.__name__)
def test_die_nutzlast_traegt_nur_primitive(case: type) -> None:
    """Kein Value Object ueber die Naht - sonst reicht die Domaene sich selbst heraus."""
    if not is_dataclass(case):
        return
    hints = get_type_hints(case)
    for field in fields(case):
        for leaf in _leaf_types(hints[field.name]):
            assert leaf in _ALLOWED_SCALARS, (
                f"{case.__name__}.{field.name} traegt {leaf!r} statt eines Primitivs"
            )


@pytest.mark.parametrize("case", error_cases(*INTERNAL_ONLY), ids=lambda case: case.__name__)
def test_interne_faelle_bleiben_ohne_code(case: type) -> None:
    """Sie erreichen den Rand nie - ein Code wuerde eine Vorlage einfordern, die niemand braucht."""
    assert not hasattr(case, "code"), (
        f"{case.__name__} traegt einen Code, erreicht den Rand aber nie. "
        "Entweder gehoert er in ERROR_UNIONS in src/main.py, oder der Code muss weg."
    )


def test_jeder_veroeffentlichte_fall_ist_benennbar() -> None:
    """Die Nutzlast eines Falls ist die Menge, aus der eine Textvorlage schoepfen darf."""
    for case in error_cases(*PUBLISHED):
        assert is_dataclass(case), f"{case.__name__} traegt keine benennbare Nutzlast"
        assert parameters_of(case) == {field.name for field in fields(case)}


def test_kein_fehlerfall_faellt_zwischen_die_mengen() -> None:
    """`DomainError` ist die Volkszaehlung - jeder Fall gehoert in genau eine Menge.

    Seit Stufe 4 von Ticket 0011 traegt jeder Domain-Port seine **eigene**,
    schmale Fehler-Union; `DomainError` ist nicht mehr der eine `E`, den alle
    sprechen, sondern die vollstaendige Aufzaehlung dessen, was es in diesem
    Context ueberhaupt gibt. Genau dafuer steht sie hier: waechst sie, wird
    dieser Test rot und verlangt die Entscheidung, ob der neue Fall
    veroeffentlicht wird, intern bleibt oder ein eigener Ausgang ist - statt dass
    er stillschweigend nirgends auftaucht.
    """
    veroeffentlicht = set(error_cases(*PUBLISHED))
    intern = set(error_cases(*INTERNAL_ONLY))
    kollision = set(error_cases(*KOLLISION))

    assert veroeffentlicht | intern | kollision == set(error_cases(DomainError))
    assert not (veroeffentlicht & intern)
    assert not (veroeffentlicht & kollision)
    assert not (intern & kollision)


@pytest.mark.parametrize("case", error_cases(*KOLLISION), ids=lambda case: case.__name__)
def test_der_eigene_ausgang_bleibt_ohne_feldfehler_code(case: type) -> None:
    """Sein Code sitzt auf der Response-Union, nicht auf der Ursache."""
    assert not hasattr(case, "code"), (
        f"{case.__name__} traegt einen Code. Veroeffentlicht wird der Fall der "
        "Response-Union (EmailAlreadyTaken), nicht die Domaenen-Ursache."
    )
