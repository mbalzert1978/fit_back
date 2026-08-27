"""Unit-Tests für Result[T, E]."""

import pytest

from src.contexts.shared_kernel.result import Err, Ok, Result


class TestOk:
    """Tests für Ok[T]."""

    def test_ok_value_access(self) -> None:
        result: Result[int, str] = Ok(42)
        assert isinstance(result, Ok)
        assert result.value == 42

    def test_ok_map(self) -> None:
        result: Result[int, str] = Ok(5)
        mapped = result.map(lambda x: x * 2)

        assert isinstance(mapped, Ok)
        assert mapped.value == 10

    def test_ok_map_changes_type(self) -> None:
        result: Result[int, str] = Ok(42)
        mapped = result.map(str)

        assert isinstance(mapped, Ok)
        assert mapped.value == "42"

    def test_ok_bind(self) -> None:
        result: Result[int, str] = Ok(5)
        bound = result.bind(lambda x: Ok(x * 2))

        assert isinstance(bound, Ok)
        assert bound.value == 10

    def test_ok_bind_to_error(self) -> None:
        result: Result[int, str] = Ok(5)
        bound = result.bind(lambda x: Err(f"Value was {x}") if x > 3 else Ok(x))

        assert isinstance(bound, Err)
        assert bound.error == "Value was 5"

    def test_ok_chaining(self) -> None:
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
        result: Result[int, str] = Err("something went wrong")
        assert isinstance(result, Err)
        assert result.error == "something went wrong"

    def test_err_map_ignored(self) -> None:
        result: Result[int, str] = Err("error")
        mapped = result.map(lambda x: x * 2)

        assert isinstance(mapped, Err)
        assert mapped.error == "error"

    def test_err_bind_ignored(self) -> None:
        result: Result[int, str] = Err("error")
        bound = result.bind(lambda x: Ok(x * 2))

        assert isinstance(bound, Err)
        assert bound.error == "error"

    def test_err_chaining(self) -> None:
        result: Result[int, str] = Err("initial error")
        chained = result.map(lambda x: x * 3).bind(lambda x: Ok(x + 4)).map(lambda x: x * 2)

        assert isinstance(chained, Err)
        assert chained.error == "initial error"


class TestResultMatching:
    """Tests für match/case Pattern-Matching."""

    def test_match_ok(self) -> None:
        result: Result[int, str] = Ok(42)

        matched_value = None
        match result:
            case Ok(value=val):
                matched_value = val
            case Err():
                pass

        assert matched_value == 42

    def test_match_err(self) -> None:
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
        seen: list[int] = []
        result: Result[int, str] = Ok(42)

        async def remember(value: int) -> None:
            seen.append(value)

        returned = await result.inspect_async(remember)

        assert seen == [42]
        assert returned is result

    @pytest.mark.asyncio
    async def test_err_loest_keine_nebenwirkung_aus(self) -> None:
        seen: list[int] = []
        result: Result[int, str] = Err("abgelehnt")

        async def remember(value: int) -> None:
            seen.append(value)

        returned = await result.inspect_async(remember)

        assert seen == []
        assert returned is result

    @pytest.mark.asyncio
    async def test_rueckgabewert_der_nebenwirkung_wird_verworfen(self) -> None:
        result: Result[int, str] = Ok(1)

        async def yields_something(_value: int) -> str:
            return "ignoriert"

        assert await result.inspect_async(yields_something) == Ok(1)


class TestBindAsync:
    """bind_async verkettet eine asynchrone Fortsetzung - und kuerzt auf Err ab."""

    @pytest.mark.asyncio
    async def test_ok_verkettet_die_asynchrone_fortsetzung(self) -> None:
        result: Result[int, str] = Ok(21)

        async def doubled(value: int) -> Result[int, str]:
            return Ok(value * 2)

        assert await result.bind_async(doubled) == Ok(42)

    @pytest.mark.asyncio
    async def test_ok_uebernimmt_auch_den_fehlschlag_der_fortsetzung(self) -> None:
        result: Result[int, str] = Ok(21)

        async def rejects(_value: int) -> Result[int, str]:
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
        result: Result[int, str] = Ok(21)

        assert result.fold(lambda value: value * 2, len) == 42

    def test_err_nimmt_den_fehler_arm(self) -> None:
        result: Result[int, str] = Err("abgelehnt")

        assert result.fold(lambda value: value * 2, len) == 9

    def test_ok_ruft_den_fehler_arm_gar_nicht_erst_auf(self) -> None:
        laeufe: list[str] = []
        result: Result[int, str] = Ok(1)

        def remember(error: str) -> int:
            laeufe.append(error)
            return 0

        assert result.fold(lambda value: value, remember) == 1
        assert laeufe == []

    def test_err_ruft_den_erfolgs_arm_gar_nicht_erst_auf(self) -> None:
        laeufe: list[int] = []
        result: Result[int, str] = Err("gescheitert")

        def remember(value: int) -> str:
            laeufe.append(value)
            return ""

        assert result.fold(remember, lambda error: error) == "gescheitert"
        assert laeufe == []

    def test_beide_arme_treffen_sich_in_einem_ergebnistyp(self) -> None:
        angenommen: Result[int, str] = Ok(7)
        abgelehnt: Result[int, str] = Err("leer")

        def beschreibe(outcome: Result[int, str]) -> str:
            return outcome.fold(lambda value: f"ok:{value}", lambda error: f"err:{error}")

        assert beschreibe(angenommen) == "ok:7"
        assert beschreibe(abgelehnt) == "err:leer"


class TestMapErr:
    """map_err transformiert den Fehler - und laesst den Erfolg in Ruhe."""

    def test_err_transformiert_den_fehler(self) -> None:
        result: Result[int, str] = Err("kaputt")

        assert result.map_err(str.upper) == Err("KAPUTT")

    def test_err_darf_den_fehlertyp_wechseln(self) -> None:
        result: Result[int, str] = Err("kaputt")

        assert result.map_err(len) == Err(6)

    def test_ok_ruft_die_transformation_gar_nicht_erst_auf(self) -> None:
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
        result: Result[int, str] = Err("kaputt")

        assert result.or_else(lambda error: Ok(len(error))) == Ok(6)

    def test_err_darf_erneut_scheitern(self) -> None:
        result: Result[int, str] = Err("kaputt")

        assert result.or_else(lambda error: Err(len(error))) == Err(6)

    def test_ok_ruft_die_alternative_gar_nicht_erst_auf(self) -> None:
        laeufe: list[str] = []
        result: Result[int, str] = Ok(1)

        def remember(error: str) -> Result[int, str]:
            laeufe.append(error)
            return Ok(0)

        returned = result.or_else(remember)

        assert laeufe == []
        assert returned is result


class TestZip:
    """Tests fuer `zip` - zwei Ausgaenge zu einem ueber ihrem Paar."""

    def test_zwei_ok_ergeben_das_paar(self) -> None:
        """Der Erfolgsfall traegt beide Werte in der Reihenfolge des Aufrufs."""
        links: Result[int, str] = Ok(1)
        rechts: Result[str, str] = Ok("zwei")

        assert links.zip(rechts) == Ok((1, "zwei"))

    def test_ein_err_links_gewinnt(self) -> None:
        links: Result[int, str] = Err("kaputt")
        rechts: Result[str, str] = Ok("zwei")

        assert links.zip(rechts) == Err("kaputt")

    def test_ein_err_rechts_gewinnt(self) -> None:
        """Auch der rechte Fehler schlaegt durch - `zip` verlangt beide Seiten."""
        links: Result[int, str] = Ok(1)
        rechts: Result[str, str] = Err("kaputt")

        assert links.zip(rechts) == Err("kaputt")

    def test_der_linke_fehler_gewinnt_gegen_den_rechten(self) -> None:
        links: Result[int, str] = Err("zuerst")
        rechts: Result[str, str] = Err("danach")

        assert links.zip(rechts) == Err("zuerst")

    def test_die_kette_tuermt_paare_auf(self) -> None:
        """`a.zip(b).zip(c)` traegt `((A, B), C)` - die Form aus Rust."""
        erst: Result[int, str] = Ok(1)
        dann: Result[str, str] = Ok("zwei")
        zuletzt: Result[float, str] = Ok(3.0)

        assert erst.zip(dann).zip(zuletzt) == Ok(((1, "zwei"), 3.0))

    def test_ein_err_am_ende_der_kette_gewinnt_auch(self) -> None:
        """Die Kette laeuft bis zum letzten Glied - nicht nur bis zum ersten Paar."""
        erst: Result[int, str] = Ok(1)
        dann: Result[str, str] = Ok("zwei")
        zuletzt: Result[float, str] = Err("kaputt")

        assert erst.zip(dann).zip(zuletzt) == Err("kaputt")


class TestZipAll:
    """Tests fuer `zip_all` - wie `zip`, aber kein Fehler geht verloren."""

    def test_zwei_ok_ergeben_das_paar(self) -> None:
        """Ohne Fehler verhaelt sich `zip_all` wie `zip`."""
        links: Result[int, list[str]] = Ok(1)
        rechts: Result[str, list[str]] = Ok("zwei")

        assert links.zip_all(rechts) == Ok((1, "zwei"))

    def test_ein_err_links_bleibt_allein(self) -> None:
        links: Result[int, list[str]] = Err(["kaputt"])
        rechts: Result[str, list[str]] = Ok("zwei")

        assert links.zip_all(rechts) == Err(["kaputt"])

    def test_ein_err_rechts_bleibt_allein(self) -> None:
        links: Result[int, list[str]] = Ok(1)
        rechts: Result[str, list[str]] = Err(["kaputt"])

        assert links.zip_all(rechts) == Err(["kaputt"])

    def test_beide_fehler_stehen_nebeneinander(self) -> None:
        """Der Unterschied zu `zip`: der zweite Befund geht nicht verloren."""
        links: Result[int, list[str]] = Err(["zuerst"])
        rechts: Result[str, list[str]] = Err(["danach"])

        assert links.zip_all(rechts) == Err(["zuerst", "danach"])

    def test_die_kette_sammelt_ueber_alle_glieder(self) -> None:
        """Drei fehlerhafte Glieder ergeben drei Befunde - in Aufrufreihenfolge."""
        erst: Result[int, list[str]] = Err(["eins"])
        dann: Result[str, list[str]] = Err(["zwei"])
        zuletzt: Result[float, list[str]] = Err(["drei"])

        assert erst.zip_all(dann).zip_all(zuletzt) == Err(["eins", "zwei", "drei"])

    def test_die_kette_tuermt_paare_auf(self) -> None:
        """Der Erfolgsfall traegt dieselbe verschachtelte Form wie bei `zip`."""
        erst: Result[int, list[str]] = Ok(1)
        dann: Result[str, list[str]] = Ok("zwei")
        zuletzt: Result[float, list[str]] = Ok(3.0)

        assert erst.zip_all(dann).zip_all(zuletzt) == Ok(((1, "zwei"), 3.0))

    def test_ein_gutes_glied_zwischen_zwei_schlechten_wird_uebersprungen(self) -> None:
        erst: Result[int, list[str]] = Err(["eins"])
        dann: Result[str, list[str]] = Ok("zwei")
        zuletzt: Result[float, list[str]] = Err(["drei"])

        assert erst.zip_all(dann).zip_all(zuletzt) == Err(["eins", "drei"])
