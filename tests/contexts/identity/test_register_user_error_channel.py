"""Der Fehlerkanal des Use Case RegisterUser deckt die Ausgaenge seiner Ports ab.

`RegisterUserError` ist bewusst ausgeschrieben (`RequestInvalid |
EmailAlreadyRegistered`) statt ueber `UserRegistryError` gebildet - der Slice
soll sich beim Wachsen der Port-Union **melden**, nicht still mitwachsen. Ohne
diesen Test schluege ein neuer Ausgang erst zur Anfragezeit im `assert_never`
auf - HTTP 500 statt roter CI.

Dieser Test **misst** die Fallmengen, statt sie zu behaupten
(`.rules/python/python-error-handling.md`, "Maschinell geprueft, nicht
erinnert"), und zwar in beiden Gliedern der Kette:

1. Jeder Ausgang von `UserRegistryError` hat einen Arm im Fehlerkanal
   `RegisterUserError`.
2. Jeder Fall von `RegisterUserError` hat einen Arm im **einen** Fold des Slice
   (`to_response`) - sonst waere der Kanal breiter als seine Auswertung.

Gelesen wird dafuer `to_response` **plus die Funktionen, die es namentlich
nennt**: seit `Result.fold` den `Ok`/`Err`-Split traegt, stehen die Arme eine
Ebene tiefer, in `_accepted` und `_rejected`. Ein Fold bleibt es trotzdem - er
ist nur nicht mehr in eine `match`-Verschachtelung gefaltet.

Bewusst **nicht** das ganze Modul: dann zaehlte jedes `case X()` irgendwo in der
Datei als behandelt, auch aus einer Funktion, die der Fold nie ruft. Die Zusage
waere breiter als ihr Gegenstand.

Waechst die Port-Union, wird hier rot, was sonst gruen bliebe. Die Aufzaehlung
selbst kommt aus `shared_kernel/coded_error.py`, wie in
`test_published_error_vocabulary.py` daneben; die Arme des Folds werden per AST
gelesen, wie in `tests/test_match_exhaustiveness.py`.
"""

import ast
import inspect
import sys
import textwrap

from src.contexts.identity.application.register_user.errors import RegisterUserError
from src.contexts.identity.application.register_user.mappers.register_user_response_mapper import (
    to_response,
)
from src.contexts.identity.domain.ports.user_registry import UserRegistryError
from src.contexts.shared_kernel.coded_error import error_cases


def _namen(*unions: object) -> set[str]:
    """Die Faelle einer Fehler-Union, auf ihre Klassennamen heruntergebrochen."""
    return {case.__name__ for case in error_cases(*unions)}


def _baum(funktion: object) -> ast.AST:
    """Der Syntaxbaum einer Funktion, unabhaengig von ihrer Einrueckung."""
    return ast.parse(textwrap.dedent(inspect.getsource(funktion)))


def _genannte_funktionen(funktion: object) -> list[object]:
    """Die Funktionen desselben Moduls, die `funktion` namentlich nennt - die Arme des Folds."""
    modul = sys.modules[to_response.__module__]
    genannt = sorted(
        knoten.id for knoten in ast.walk(_baum(funktion)) if isinstance(knoten, ast.Name)
    )
    kandidaten = (getattr(modul, name, None) for name in genannt)
    return [kandidat for kandidat in kandidaten if inspect.isfunction(kandidat)]


def _arme_des_folds() -> set[str]:
    """Die Klassen, auf die der Fold des Slice matcht - gelesen aus ihm und seinen Armen."""
    return {
        knoten.cls.id
        for funktion in (to_response, *_genannte_funktionen(to_response))
        for knoten in ast.walk(_baum(funktion))
        if isinstance(knoten, ast.MatchClass) and isinstance(knoten.cls, ast.Name)
    }


def test_jeder_ausgang_des_ports_hat_einen_arm_im_fehlerkanal() -> None:
    """Waechst `UserRegistryError`, muss `RegisterUserError` mitgezogen werden."""
    fehlend = sorted(_namen(UserRegistryError) - _namen(RegisterUserError))

    assert not fehlend, (
        f"Diese Ausgaenge von UserRegistryError fehlen im Fehlerkanal des Use Case: {fehlend}. "
        "Der Handler kann sie liefern, `RegisterUserError` kennt sie nicht - der Fall faellt "
        "erst zur Anfragezeit ins `assert_never` von `to_response`. Aufnehmen in "
        "src/contexts/identity/application/register_user/errors.py."
    )


def test_jeder_fall_des_fehlerkanals_hat_einen_arm_im_fold() -> None:
    """Der eine Fold des Slice wertet den Kanal vollstaendig aus, nicht nur teilweise."""
    unbehandelt = sorted(_namen(RegisterUserError) - _arme_des_folds())

    assert not unbehandelt, (
        f"Diese Faelle von RegisterUserError haben keinen Arm in `to_response`: {unbehandelt}. "
        "Sie erreichen den Fold und landen dort im `assert_never` - also im HTTP-500 statt in "
        "einer Antwort. Arm ergaenzen in "
        "src/contexts/identity/application/register_user/mappers/register_user_response_mapper.py."
    )
