"""Unit-Tests für Result[T, E]."""

import pytest

from src.contexts.shared_kernel.result import Err, Ok, Result


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
        chained = result.map(lambda x: x * 3).bind(lambda x: Ok(x + 4)).map(lambda x: x * 2)

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


class TestInspectAsync:
    """inspect_async loest eine Nebenwirkung aus, ohne die Kette zu veraendern."""

    @pytest.mark.asyncio
    async def test_ok_loest_die_nebenwirkung_aus_und_bleibt_unveraendert(self) -> None:
        """Auf Ok laeuft die Nebenwirkung, das Result kommt identisch zurueck."""
        seen: list[int] = []
        result: Result[int, str] = Ok(42)

        async def remember(value: int) -> None:
            seen.append(value)

        returned = await result.inspect_async(remember)

        assert seen == [42]
        assert returned is result

    @pytest.mark.asyncio
    async def test_err_loest_keine_nebenwirkung_aus(self) -> None:
        """Auf Err bleibt die Nebenwirkung aus - es gibt keinen Erfolgs-Wert."""
        seen: list[int] = []
        result: Result[int, str] = Err("abgelehnt")

        async def remember(value: int) -> None:
            seen.append(value)

        returned = await result.inspect_async(remember)

        assert seen == []
        assert returned is result

    @pytest.mark.asyncio
    async def test_rueckgabewert_der_nebenwirkung_wird_verworfen(self) -> None:
        """Was `f` zurueckgibt, ist ohne Belang - sonst waere `bind` das richtige Werkzeug."""
        result: Result[int, str] = Ok(1)

        async def yields_something(value: int) -> str:
            return "ignoriert"

        assert await result.inspect_async(yields_something) == Ok(1)


class TestBindAsync:
    """bind_async verkettet eine asynchrone Fortsetzung - und kuerzt auf Err ab."""

    @pytest.mark.asyncio
    async def test_ok_verkettet_die_asynchrone_fortsetzung(self) -> None:
        """Auf Ok laeuft die Fortsetzung und ihr Result ist das Ergebnis."""
        result: Result[int, str] = Ok(21)

        async def doubled(value: int) -> Result[int, str]:
            return Ok(value * 2)

        assert await result.bind_async(doubled) == Ok(42)

    @pytest.mark.asyncio
    async def test_ok_uebernimmt_auch_den_fehlschlag_der_fortsetzung(self) -> None:
        """Die Fortsetzung darf scheitern - dann ist ihr Err das Ergebnis."""
        result: Result[int, str] = Ok(21)

        async def rejects(value: int) -> Result[int, str]:
            return Err("abgelehnt")

        assert await result.bind_async(rejects) == Err("abgelehnt")

    @pytest.mark.asyncio
    async def test_err_ruft_die_fortsetzung_gar_nicht_erst_auf(self) -> None:
        """Die Abkuerzung, von der die Behavior-Kette lebt."""
        laeufe: list[int] = []
        result: Result[int, str] = Err("schon gescheitert")

        async def remember(value: int) -> Result[int, str]:
            laeufe.append(value)
            return Ok(value)

        returned = await result.bind_async(remember)

        assert laeufe == []
        assert returned is result


class TestFold:
    """fold fuehrt kontrolliert aus dem Result heraus - der Eliminator."""

    def test_ok_nimmt_den_erfolgs_arm(self) -> None:
        """Auf Ok laeuft on_ok und sein Rueckgabewert ist das Ergebnis."""
        result: Result[int, str] = Ok(21)

        assert result.fold(lambda value: value * 2, len) == 42

    def test_err_nimmt_den_fehler_arm(self) -> None:
        """Auf Err laeuft on_err und sein Rueckgabewert ist das Ergebnis."""
        result: Result[int, str] = Err("abgelehnt")

        assert result.fold(lambda value: value * 2, len) == 9

    def test_ok_ruft_den_fehler_arm_gar_nicht_erst_auf(self) -> None:
        """Nur ein Arm laeuft - der andere wird nie ausgewertet."""
        laeufe: list[str] = []
        result: Result[int, str] = Ok(1)

        def remember(error: str) -> int:
            laeufe.append(error)
            return 0

        assert result.fold(lambda value: value, remember) == 1
        assert laeufe == []

    def test_err_ruft_den_erfolgs_arm_gar_nicht_erst_auf(self) -> None:
        """Nur ein Arm laeuft - der andere wird nie ausgewertet."""
        laeufe: list[int] = []
        result: Result[int, str] = Err("gescheitert")

        def remember(value: int) -> str:
            laeufe.append(value)
            return ""

        assert result.fold(remember, lambda error: error) == "gescheitert"
        assert laeufe == []

    def test_beide_arme_treffen_sich_in_einem_ergebnistyp(self) -> None:
        """Der Sinn des Eliminators: zwei Ausgaenge, eine Antwort-Union."""
        angenommen: Result[int, str] = Ok(7)
        abgelehnt: Result[int, str] = Err("leer")

        def beschreibe(outcome: Result[int, str]) -> str:
            return outcome.fold(lambda value: f"ok:{value}", lambda error: f"err:{error}")

        assert beschreibe(angenommen) == "ok:7"
        assert beschreibe(abgelehnt) == "err:leer"


class TestMapErr:
    """map_err transformiert den Fehler - und laesst den Erfolg in Ruhe."""

    def test_err_transformiert_den_fehler(self) -> None:
        """Auf Err laeuft die Transformation und ersetzt den Fehlerwert."""
        result: Result[int, str] = Err("kaputt")

        assert result.map_err(str.upper) == Err("KAPUTT")

    def test_err_darf_den_fehlertyp_wechseln(self) -> None:
        """Der neue Fehler muss nicht denselben Typ haben wie der alte."""
        result: Result[int, str] = Err("kaputt")

        assert result.map_err(len) == Err(6)

    def test_ok_ruft_die_transformation_gar_nicht_erst_auf(self) -> None:
        """Es liegt kein Fehler vor - die Transformation laeuft nicht."""
        laeufe: list[str] = []
        result: Result[int, str] = Ok(1)

        def remember(error: str) -> str:
            laeufe.append(error)
            return error

        returned = result.map_err(remember)

        assert laeufe == []
        assert returned is result


class TestOrElse:
    """or_else ist das Gegenstueck zu bind auf dem Fehler-Zweig."""

    def test_err_nimmt_die_alternative(self) -> None:
        """Auf Err laeuft die Alternative und darf den Ausgang drehen."""
        result: Result[int, str] = Err("kaputt")

        assert result.or_else(lambda error: Ok(len(error))) == Ok(6)

    def test_err_darf_erneut_scheitern(self) -> None:
        """Die Alternative darf selbst einen neuen Fehler liefern."""
        result: Result[int, str] = Err("kaputt")

        assert result.or_else(lambda error: Err(len(error))) == Err(6)

    def test_ok_ruft_die_alternative_gar_nicht_erst_auf(self) -> None:
        """Es liegt kein Fehler vor - die Alternative laeuft nicht."""
        laeufe: list[str] = []
        result: Result[int, str] = Ok(1)

        def remember(error: str) -> Result[int, str]:
            laeufe.append(error)
            return Ok(0)

        returned = result.or_else(remember)

        assert laeufe == []
        assert returned is result
