"""Welche Domaenenfehler der Response-Mapper von RegisterUser ueberhaupt sehen kann.

`to_response` behandelt genau zwei Ausgaenge und laesst alles andere als
`PipelineBroken` scheitern. Das ist nur richtig, solange die Pipeline die uebrigen
Faelle wirklich ausschliesst - sie validiert vollstaendig und baut das Command
danach mit `hydrate`, sodass kein Value-Object-Fehler den Handler erreicht.

Dieser Test ist die Absicherung dieser Annahme, und er ersetzt ein Versprechen,
das der Code vorher nicht halten konnte: ein vollzaehliges `match` ohne
Auffangzweig faengt einen neu hinzugekommenen Fall in Python **nicht** ab - der
`match` faellt still durch und die Funktion gibt `None` zurueck. Ein Typpruefer
wuerde das melden, dieses Repo faehrt bewusst ohne einen.

Waechst `DomainError`, wird der Test rot und verlangt eine Entscheidung: gehoert
der neue Fall in die Antwort (dann in `MAPPED` und in `to_response`), oder
schliesst die Pipeline ihn aus (dann in `UNREACHABLE`)? Beides stillschweigend
offen zu lassen, ist danach nicht mehr moeglich.
"""

import pytest

from src.contexts.identity.application.register_user.adapters import IdnEncoderAdapter
from src.contexts.identity.application.register_user.fakes import PassthroughIdnLabels
from src.contexts.identity.application.register_user.mappers.register_user_response_mapper import (
    PipelineBroken,
    to_response,
)
from src.contexts.identity.domain import (
    DomainError,
    Email,
    EmailAlreadyRegistered,
    PasswordTooShort,
    UserIdMalformed,
)
from src.contexts.shared_kernel import Err
from src.contexts.shared_kernel.coded_error import error_cases

MAPPED = {EmailAlreadyRegistered}
"""Faelle, fuer die `to_response` eine eigene Antwort kennt."""

UNREACHABLE = set(error_cases(DomainError)) - MAPPED
"""Alles Uebrige - von der Pipeline ausgeschlossen, siehe Modul-Docstring."""


def test_jeder_domaenenfehler_ist_entweder_abgebildet_oder_ausgeschlossen() -> None:
    """Kein Fall darf unbemerkt zwischen beiden Mengen hindurchfallen."""
    alle = set(error_cases(DomainError))
    assert MAPPED | UNREACHABLE == alle
    assert not (MAPPED & UNREACHABLE)


def test_ein_abgebildeter_fall_wird_nicht_als_bug_behandelt() -> None:
    """`EmailAlreadyRegistered` ist ein Fachfall und muss eine Antwort ergeben."""
    email = Email.hydrate("someone@example.com", IdnEncoderAdapter(PassthroughIdnLabels()))
    antwort = to_response(Err(EmailAlreadyRegistered(email)))

    assert antwort.code == "email-already-registered"
    assert antwort.email == "someone@example.com"


@pytest.mark.parametrize(
    "error",
    [PasswordTooShort(actual_length=3, minimum=8), UserIdMalformed(candidate="keine-uuid")],
    ids=lambda error: type(error).__name__,
)
def test_ein_ausgeschlossener_fall_scheitert_laut(error: DomainError) -> None:
    """Er darf nicht als Feldfehler zurueckuebersetzt werden - das verschleierte den Bug."""
    assert type(error) in UNREACHABLE

    with pytest.raises(PipelineBroken) as scheitern:
        to_response(Err(error))

    assert scheitern.value.error is error
    assert type(error).__name__ in str(scheitern.value)
