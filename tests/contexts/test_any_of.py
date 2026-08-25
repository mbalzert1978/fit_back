"""Der ODER-Kombinator `any_of` - der erste passende Zweig gewinnt."""

from src.contexts.shared_kernel import Err, Ok, Result
from src.contexts.shared_kernel.validation import any_of


def test_first_matching_branch_wins_and_the_later_ones_do_not_run() -> None:
    """Beleg: nach einem Treffer laeuft kein weiterer Zweig."""
    laeufe: list[str] = []

    def trifft(value: str) -> Result[str, str]:
        laeufe.append("trifft")
        return Ok(value)

    def laeuft_nie(value: str) -> Result[str, str]:
        laeufe.append("laeuft_nie")
        return Ok(value)

    assert any_of(trifft, laeuft_nie)("wert") == Ok("wert")
    assert laeufe == ["trifft"]


def test_the_winning_branch_hands_on_its_own_value() -> None:
    """Beleg: ein Zweig darf normalisieren - weitergereicht wird sein Ergebnis."""

    def scheitert(_: str) -> Result[str, str]:
        return Err("erster")

    def normalisiert(value: str) -> Result[str, str]:
        return Ok(value.upper())

    assert any_of(scheitert, normalisiert)("wert") == Ok("WERT")


def test_without_a_match_the_last_error_survives() -> None:
    """Beleg: scheitern alle Zweige, traegt das Ergebnis den Fehler des letzten."""

    def erster(_: str) -> Result[str, str]:
        return Err("erster")

    def letzter(_: str) -> Result[str, str]:
        return Err("letzter")

    assert any_of(erster, letzter)("wert") == Err("letzter")


def test_a_single_branch_behaves_like_the_rule_itself() -> None:
    """Beleg: ein Zweig allein ist zulaessig und aendert nichts."""

    def trifft(value: str) -> Result[str, str]:
        return Ok(value)

    assert any_of(trifft)("wert") == Ok("wert")
