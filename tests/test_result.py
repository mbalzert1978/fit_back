"""Unit-Tests für Result[T, E]."""

from src.shared_kernel.result import Err, Ok, Result


class TestOk:
    """Tests für Ok[T]."""

    def test_ok_value_access(self) -> None:
        """Ok sollte den Wert speichern und zurückgeben."""
        result: Result[int, str] = Ok(42)
        assert isinstance(result, Ok)
        assert result.value == 42

    def test_ok_map(self) -> None:
        """map() sollte eine Funktion auf den Ok-Wert anwenden."""
        result: Result[int, str] = Ok(5)
        mapped = result.map(lambda x: x * 2)

        assert isinstance(mapped, Ok)
        assert mapped.value == 10

    def test_ok_map_changes_type(self) -> None:
        """map() sollte den Ergebnis-Typ ändern können."""
        result: Result[int, str] = Ok(42)
        mapped = result.map(str)

        assert isinstance(mapped, Ok)
        assert mapped.value == "42"

    def test_ok_bind(self) -> None:
        """bind() sollte eine Funktion mit Result-Rückgabe verketten."""
        result: Result[int, str] = Ok(5)
        bound = result.bind(lambda x: Ok(x * 2))

        assert isinstance(bound, Ok)
        assert bound.value == 10

    def test_ok_bind_to_error(self) -> None:
        """bind() sollte das Result der Funktion zurückgeben (auch bei Err)."""
        result: Result[int, str] = Ok(5)
        bound = result.bind(lambda x: Err(f"Value was {x}") if x > 3 else Ok(x))

        assert isinstance(bound, Err)
        assert bound.error == "Value was 5"

    def test_ok_chaining(self) -> None:
        """map() und bind() sollten verkettbar sein."""
        result: Result[int, str] = Ok(2)
        chained = (
            result.map(lambda x: x * 3)  # 6
            .bind(lambda x: Ok(x + 4))  # 10
            .map(lambda x: x * 2)  # 20
        )

        assert isinstance(chained, Ok)
        assert chained.value == 20


class TestErr:
    """Tests für Err[E]."""

    def test_err_error_access(self) -> None:
        """Err sollte den Fehler speichern und zurückgeben."""
        result: Result[int, str] = Err("something went wrong")
        assert isinstance(result, Err)
        assert result.error == "something went wrong"

    def test_err_map_ignored(self) -> None:
        """map() auf Err sollte Err unverändert zurückgeben."""
        result: Result[int, str] = Err("error")
        mapped = result.map(lambda x: x * 2)

        assert isinstance(mapped, Err)
        assert mapped.error == "error"

    def test_err_bind_ignored(self) -> None:
        """bind() auf Err sollte Err unverändert zurückgeben."""
        result: Result[int, str] = Err("error")
        bound = result.bind(lambda x: Ok(x * 2))

        assert isinstance(bound, Err)
        assert bound.error == "error"

    def test_err_chaining(self) -> None:
        """Chaining über Err sollte Err propagieren."""
        result: Result[int, str] = Err("initial error")
        chained = (
            result.map(lambda x: x * 3)
            .bind(lambda x: Ok(x + 4))
            .map(lambda x: x * 2)
        )

        assert isinstance(chained, Err)
        assert chained.error == "initial error"


class TestResultMatching:
    """Tests für match/case Pattern-Matching."""

    def test_match_ok(self) -> None:
        """match/case sollte Ok korrekt unterscheiden."""
        result: Result[int, str] = Ok(42)

        matched_value = None
        match result:
            case Ok(value=val):
                matched_value = val
            case Err():
                pass

        assert matched_value == 42

    def test_match_err(self) -> None:
        """match/case sollte Err korrekt unterscheiden."""
        result: Result[int, str] = Err("test error")

        matched_error = None
        match result:
            case Ok():
                pass
            case Err(error=err):
                matched_error = err

        assert matched_error == "test error"
