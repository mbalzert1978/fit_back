"""Unit-Tests fuer die async-Kette: `AsyncResult` und die `_async`-Arme auf `Ok`/`Err`.

Gepruefte Zusage: eine Kette bleibt bis zum Schluss chainbar, es steht **ein**
`await` am Ende, und ein `Err` kuerzt jeden weiteren Schritt ab - genau wie in
der sync-Variante.
"""

import inspect

import pytest

from src.contexts.shared_kernel.result import AsyncResult, Err, Ok, Result

# --- Hilfen ------------------------------------------------------------------


async def _pending[T, E](outcome: Result[T, E]) -> Result[T, E]:
    """Ein `Result`, das erst nach einem `await` vorliegt - der Einstieg in eine Kette."""
    return outcome


class Spion:
    """Haelt fest, welche Schritte wirklich gelaufen sind."""

    def __init__(self) -> None:
        self.laeufe: list[str] = []

    def merke(self, name: str) -> None:
        """Halte einen gelaufenen Schritt fest."""
        self.laeufe.append(name)


# --- Die async-Arme auf Ok ---------------------------------------------------


class TestOkAsyncArme:
    """Auf `Ok` laufen die Erfolgs-Arme; die Fehler-Arme werden nie aufgerufen."""

    @pytest.mark.asyncio
    async def test_map_async_transformiert_den_wert(self) -> None:
        """map_async hebt eine asynchrone Funktion auf den Erfolgs-Wert."""

        async def verdoppelt(value: int) -> int:
            return value * 2

        assert await Ok(21).map_async(verdoppelt) == Ok(42)

    @pytest.mark.asyncio
    async def test_map_err_async_wird_uebersprungen(self) -> None:
        """Es liegt kein Fehler vor - die Transformation laeuft nicht."""
        spion = Spion()

        async def nie(error: str) -> str:
            spion.merke("map_err_async")
            return error

        assert await Ok(1).map_err_async(nie) == Ok(1)
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_or_else_async_wird_uebersprungen(self) -> None:
        """Es liegt kein Fehler vor - die Alternative laeuft nicht."""
        spion = Spion()

        async def nie(error: str) -> Result[int, str]:
            spion.merke("or_else_async")
            return Ok(0)

        assert await Ok(1).or_else_async(nie) == Ok(1)
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_fold_async_nimmt_den_erfolgs_arm(self) -> None:
        """Nur der Erfolgs-Arm laeuft, und sein Wert ist das Ergebnis."""
        spion = Spion()

        async def angenommen(value: int) -> str:
            return f"ok:{value}"

        async def abgelehnt(error: str) -> str:
            spion.merke("fold_async:err")
            return f"err:{error}"

        assert await Ok(7).fold_async(angenommen, abgelehnt) == "ok:7"
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_bind_async_bleibt_chainbar(self) -> None:
        """Das Ergebnis ist eine Kette, kein fertiges Result - hier haengt der naechste Schritt an."""
        kette = Ok(21).bind_async(lambda value: _pending(Ok(value * 2)))

        assert isinstance(kette, AsyncResult)
        assert await kette.map(str) == Ok("42")

    @pytest.mark.asyncio
    async def test_inspect_async_bleibt_chainbar(self) -> None:
        """Die Nebenwirkung laeuft, der Ausgang bleibt unveraendert und die Kette offen."""
        spion = Spion()

        async def melde(value: int) -> None:
            spion.merke(f"melde({value})")

        assert await Ok(5).inspect_async(melde).map(lambda value: value + 1) == Ok(6)
        assert spion.laeufe == ["melde(5)"]


# --- Die async-Arme auf Err --------------------------------------------------


class TestErrAsyncArme:
    """Auf `Err` laufen die Fehler-Arme; die Erfolgs-Arme werden nie aufgerufen."""

    @pytest.mark.asyncio
    async def test_map_async_wird_uebersprungen(self) -> None:
        """Es liegt kein Erfolgs-Wert vor - die Transformation laeuft nicht."""
        spion = Spion()

        async def nie(value: int) -> int:
            spion.merke("map_async")
            return value

        assert await Err("kaputt").map_async(nie) == Err("kaputt")
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_bind_async_wird_uebersprungen(self) -> None:
        """Der Kurzschluss: die Fortsetzung wird nie erzeugt und nie erwartet."""
        spion = Spion()

        async def nie(value: int) -> Result[int, str]:
            spion.merke("bind_async")
            return Ok(value)

        assert await Err("kaputt").bind_async(nie) == Err("kaputt")
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_map_err_async_transformiert_den_fehler(self) -> None:
        """map_err_async hebt eine asynchrone Funktion auf den Fehler."""

        async def laut(error: str) -> str:
            return error.upper()

        assert await Err("kaputt").map_err_async(laut) == Err("KAPUTT")

    @pytest.mark.asyncio
    async def test_or_else_async_nimmt_die_alternative(self) -> None:
        """Die Alternative darf den Fehlschlag in einen Erfolg drehen."""

        async def rettung(error: str) -> Result[int, str]:
            return Ok(len(error))

        assert await Err("kaputt").or_else_async(rettung) == Ok(6)

    @pytest.mark.asyncio
    async def test_or_else_async_darf_erneut_scheitern(self) -> None:
        """Die Alternative darf auch einen neuen Fehler liefern."""

        async def schlaegt_fehl(error: str) -> Result[int, int]:
            return Err(len(error))

        assert await Err("kaputt").or_else_async(schlaegt_fehl) == Err(6)

    @pytest.mark.asyncio
    async def test_fold_async_nimmt_den_fehler_arm(self) -> None:
        """Nur der Fehler-Arm laeuft, und sein Wert ist das Ergebnis."""
        spion = Spion()

        async def angenommen(value: int) -> str:
            spion.merke("fold_async:ok")
            return f"ok:{value}"

        async def abgelehnt(error: str) -> str:
            return f"err:{error}"

        assert await Err("leer").fold_async(angenommen, abgelehnt) == "err:leer"
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_inspect_async_loest_keine_nebenwirkung_aus(self) -> None:
        """Es liegt kein Erfolgs-Wert vor - gemeldet wird nichts."""
        spion = Spion()

        async def melde(value: int) -> None:
            spion.merke("melde")

        assert await Err("kaputt").inspect_async(melde) == Err("kaputt")
        assert spion.laeufe == []


# --- AsyncResult: der Ausgang der Kette --------------------------------------


class TestAsyncResultAwait:
    """`await` loest die Kette aus und liefert den fertigen Ausgang."""

    @pytest.mark.asyncio
    async def test_erfolg_kommt_durch(self) -> None:
        """Aus einem ausstehenden Ok wird nach dem await ein Ok."""
        assert await AsyncResult(_pending(Ok(1))) == Ok(1)

    @pytest.mark.asyncio
    async def test_fehlschlag_kommt_durch(self) -> None:
        """Aus einem ausstehenden Err wird nach dem await ein Err."""
        assert await AsyncResult(_pending(Err("kaputt"))) == Err("kaputt")


# --- AsyncResult: jedes Kettenglied, beide Ausgaenge -------------------------


class TestAsyncResultKettenglieder:
    """Jede Methode von `AsyncResult` - einmal auf dem Ok-, einmal auf dem Err-Zweig."""

    @pytest.mark.asyncio
    async def test_map_auf_ok(self) -> None:
        """map hebt eine sync-Funktion auf den ausstehenden Erfolgs-Wert."""
        assert await AsyncResult(_pending(Ok(21))).map(lambda value: value * 2) == Ok(42)

    @pytest.mark.asyncio
    async def test_map_auf_err(self) -> None:
        """Auf dem Fehler-Zweig laeuft die Funktion nicht."""
        spion = Spion()

        def nie(value: int) -> int:
            spion.merke("map")
            return value

        assert await AsyncResult(_pending(Err("kaputt"))).map(nie) == Err("kaputt")
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_map_async_auf_ok(self) -> None:
        """map_async hebt eine async-Funktion auf den ausstehenden Erfolgs-Wert."""

        async def verdoppelt(value: int) -> int:
            return value * 2

        assert await AsyncResult(_pending(Ok(21))).map_async(verdoppelt) == Ok(42)

    @pytest.mark.asyncio
    async def test_map_async_auf_err(self) -> None:
        """Auf dem Fehler-Zweig laeuft die Funktion nicht."""
        spion = Spion()

        async def nie(value: int) -> int:
            spion.merke("map_async")
            return value

        assert await AsyncResult(_pending(Err("kaputt"))).map_async(nie) == Err("kaputt")
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_bind_auf_ok(self) -> None:
        """bind verkettet eine sync-Funktion, die selbst ein Result liefert."""
        kette = AsyncResult(_pending(Ok(21))).bind(lambda value: Ok(value * 2))

        assert await kette == Ok(42)

    @pytest.mark.asyncio
    async def test_bind_darf_scheitern(self) -> None:
        """Der verkettete Schritt darf den Ausgang auf Err drehen."""
        kette = AsyncResult(_pending(Ok(21))).bind(lambda value: Err(f"zu gross: {value}"))

        assert await kette == Err("zu gross: 21")

    @pytest.mark.asyncio
    async def test_bind_auf_err(self) -> None:
        """Auf dem Fehler-Zweig laeuft die Fortsetzung nicht."""
        spion = Spion()

        def nie(value: int) -> Result[int, str]:
            spion.merke("bind")
            return Ok(value)

        assert await AsyncResult(_pending(Err("kaputt"))).bind(nie) == Err("kaputt")
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_bind_async_auf_ok(self) -> None:
        """bind_async verkettet eine async-Funktion, die selbst ein Result liefert."""

        async def verdoppelt(value: int) -> Result[int, str]:
            return Ok(value * 2)

        assert await AsyncResult(_pending(Ok(21))).bind_async(verdoppelt) == Ok(42)

    @pytest.mark.asyncio
    async def test_bind_async_auf_err(self) -> None:
        """Auf dem Fehler-Zweig laeuft die Fortsetzung nicht."""
        spion = Spion()

        async def nie(value: int) -> Result[int, str]:
            spion.merke("bind_async")
            return Ok(value)

        assert await AsyncResult(_pending(Err("kaputt"))).bind_async(nie) == Err("kaputt")
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_map_err_auf_err(self) -> None:
        """map_err transformiert den ausstehenden Fehler."""
        kette = AsyncResult(_pending(Err("kaputt"))).map_err(str.upper)

        assert await kette == Err("KAPUTT")

    @pytest.mark.asyncio
    async def test_map_err_auf_ok(self) -> None:
        """Auf dem Erfolgs-Zweig laeuft die Transformation nicht."""
        spion = Spion()

        def nie(error: str) -> str:
            spion.merke("map_err")
            return error

        assert await AsyncResult(_pending(Ok(1))).map_err(nie) == Ok(1)
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_map_err_async_auf_err(self) -> None:
        """map_err_async transformiert den ausstehenden Fehler asynchron."""

        async def laut(error: str) -> str:
            return error.upper()

        assert await AsyncResult(_pending(Err("kaputt"))).map_err_async(laut) == Err("KAPUTT")

    @pytest.mark.asyncio
    async def test_map_err_async_auf_ok(self) -> None:
        """Auf dem Erfolgs-Zweig laeuft die Transformation nicht."""
        spion = Spion()

        async def nie(error: str) -> str:
            spion.merke("map_err_async")
            return error

        assert await AsyncResult(_pending(Ok(1))).map_err_async(nie) == Ok(1)
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_or_else_auf_err(self) -> None:
        """or_else darf den ausstehenden Fehlschlag in einen Erfolg drehen."""
        kette = AsyncResult(_pending(Err("kaputt"))).or_else(lambda error: Ok(len(error)))

        assert await kette == Ok(6)

    @pytest.mark.asyncio
    async def test_or_else_auf_ok(self) -> None:
        """Auf dem Erfolgs-Zweig laeuft die Alternative nicht."""
        spion = Spion()

        def nie(error: str) -> Result[int, str]:
            spion.merke("or_else")
            return Ok(0)

        assert await AsyncResult(_pending(Ok(1))).or_else(nie) == Ok(1)
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_or_else_async_auf_err(self) -> None:
        """or_else_async darf den ausstehenden Fehlschlag asynchron auffangen."""

        async def rettung(error: str) -> Result[int, str]:
            return Ok(len(error))

        assert await AsyncResult(_pending(Err("kaputt"))).or_else_async(rettung) == Ok(6)

    @pytest.mark.asyncio
    async def test_or_else_async_auf_ok(self) -> None:
        """Auf dem Erfolgs-Zweig laeuft die Alternative nicht."""
        spion = Spion()

        async def nie(error: str) -> Result[int, str]:
            spion.merke("or_else_async")
            return Ok(0)

        assert await AsyncResult(_pending(Ok(1))).or_else_async(nie) == Ok(1)
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_inspect_async_auf_ok(self) -> None:
        """Die Nebenwirkung laeuft, der Ausgang bleibt unveraendert."""
        spion = Spion()

        async def melde(value: int) -> None:
            spion.merke(f"melde({value})")

        assert await AsyncResult(_pending(Ok(5))).inspect_async(melde) == Ok(5)
        assert spion.laeufe == ["melde(5)"]

    @pytest.mark.asyncio
    async def test_inspect_async_auf_err(self) -> None:
        """Auf dem Fehler-Zweig laeuft die Nebenwirkung nicht."""
        spion = Spion()

        async def melde(value: int) -> None:
            spion.merke("melde")

        assert await AsyncResult(_pending(Err("kaputt"))).inspect_async(melde) == Err("kaputt")
        assert spion.laeufe == []

    @pytest.mark.asyncio
    async def test_fold_faltet_beide_ausgaenge(self) -> None:
        """fold ist der Ausgang der Kette: zwei Zweige, ein Wert."""

        def beschreibe_ok(value: int) -> str:
            return f"ok:{value}"

        def beschreibe_err(error: str) -> str:
            return f"err:{error}"

        angenommen = AsyncResult(_pending(Ok(7)))
        abgelehnt: AsyncResult[int, str] = AsyncResult(_pending(Err("leer")))

        assert await angenommen.fold(beschreibe_ok, beschreibe_err) == "ok:7"
        assert await abgelehnt.fold(beschreibe_ok, beschreibe_err) == "err:leer"

    @pytest.mark.asyncio
    async def test_fold_async_faltet_beide_ausgaenge(self) -> None:
        """fold_async ist derselbe Ausgang, nur mit asynchronen Armen."""

        async def beschreibe_ok(value: int) -> str:
            return f"ok:{value}"

        async def beschreibe_err(error: str) -> str:
            return f"err:{error}"

        angenommen = AsyncResult(_pending(Ok(7)))
        abgelehnt: AsyncResult[int, str] = AsyncResult(_pending(Err("leer")))

        assert await angenommen.fold_async(beschreibe_ok, beschreibe_err) == "ok:7"
        assert await abgelehnt.fold_async(beschreibe_ok, beschreibe_err) == "err:leer"


# --- Die Kette am Stueck -----------------------------------------------------


class TestKetteAmStueck:
    """Die eigentliche Zusage: chainbar bis zum Schluss, ein `await`, Kurzschluss auf Err."""

    @pytest.mark.asyncio
    async def test_das_csharp_vorbild(self) -> None:
        """`await selfTask.MapAsync(v => v * 2).BindAsync(v => SomeFn(v))` auf Python."""

        async def some_fn_returning_result(value: int) -> Result[str, str]:
            return Ok(f"#{value}")

        self_task = _pending(Ok(21))

        got = await AsyncResult(self_task).map(lambda v: v * 2).bind_async(some_fn_returning_result)

        assert got == Ok("#42")

    @pytest.mark.asyncio
    async def test_err_kurzschliesst_mitten_in_der_kette(self) -> None:
        """Ab dem ersten Err laeuft kein weiterer Schritt an."""
        spion = Spion()

        def erster_schritt(value: int) -> Result[int, str]:
            spion.merke("erster")
            return Ok(value + 1)

        def bricht_ab(value: int) -> Result[int, str]:
            spion.merke("bricht_ab")
            return Err(f"abgelehnt bei {value}")

        async def danach(value: int) -> Result[int, str]:
            spion.merke("danach")
            return Ok(value)

        def auch_danach(value: int) -> int:
            spion.merke("auch_danach")
            return value

        got = await (
            AsyncResult(_pending(Ok(1)))
            .bind(erster_schritt)
            .bind(bricht_ab)
            .bind_async(danach)
            .map(auch_danach)
        )

        assert got == Err("abgelehnt bei 2")
        assert spion.laeufe == ["erster", "bricht_ab"]

    @pytest.mark.asyncio
    async def test_sync_und_async_schritte_gemischt(self) -> None:
        """Eine Kette darf sync- und async-Schritte mischen - ein `await` am Ende."""
        spion = Spion()

        async def async_schritt(value: int) -> int:
            spion.merke("async_schritt")
            return value + 1

        async def async_verkettung(value: int) -> Result[int, str]:
            spion.merke("async_verkettung")
            return Ok(value * 10)

        def sync_verkettung(value: int) -> Result[int, str]:
            spion.merke("sync_verkettung")
            return Ok(value - 3)

        got = await (
            AsyncResult(_pending(Ok(2)))
            .map(lambda value: value * 5)
            .map_async(async_schritt)
            .bind(sync_verkettung)
            .bind_async(async_verkettung)
            .map(str)
        )

        assert got == Ok("80")
        assert spion.laeufe == ["async_schritt", "sync_verkettung", "async_verkettung"]

    @pytest.mark.asyncio
    async def test_der_fehler_darf_unterwegs_uebersetzt_werden(self) -> None:
        """map_err und or_else haengen genauso in der Kette wie die Erfolgs-Schritte."""
        got = await (
            AsyncResult(_pending(Ok(1)))
            .bind(lambda value: Err(f"nein:{value}"))
            .map_err(str.upper)
            .or_else(lambda error: Ok(len(error)))
            .map(lambda laenge: laenge * 2)
        )

        assert got == Ok(12)


# --- Die drei Traeger bleiben deckungsgleich ---------------------------------


def _kombinatoren(traeger: type) -> set[str]:
    """Die public Kombinatoren eines Traegers - Felder und Dunder zaehlen nicht."""
    return {
        name
        for name, member in vars(traeger).items()
        if not name.startswith("_") and inspect.isfunction(member)
    }


class TestDieDreiTraegerBleibenDeckungsgleich:
    """Ein Kombinator lebt auf `Ok`, `Err` **und** `AsyncResult` - oder auf keinem.

    Ein neuer Kombinator kostet drei Aenderungen an drei Stellen. Zwei davon
    sind der Summentyp selbst und nicht zu vermeiden; die dritte ist seit
    `_then`/`_then_async` eine Zeile - und genau deshalb leicht zu vergessen.
    Vergessen wird hier rot, statt beim Lesen aufzufallen
    (`.rules/python/python-error-handling.md`, "Maschinell geprueft, nicht
    erinnert").
    """

    def test_jeder_kombinator_von_ok_und_err_liegt_auch_auf_async_result(self) -> None:
        """Was der fertige Ausgang kann, kann die ausstehende Kette auch."""
        fehlend = sorted((_kombinatoren(Ok) | _kombinatoren(Err)) - _kombinatoren(AsyncResult))

        assert not fehlend, (
            f"Diese Kombinatoren fehlen auf `AsyncResult`: {fehlend}. Eine Kette bricht damit "
            "an dieser Stelle ab - der Aufrufer muesste in der Mitte `await`en, und genau das "
            "soll die Kette loswerden. Ergaenzen in src/contexts/shared_kernel/result.py, je "
            "eine Zeile ueber `_then` oder `_then_async`."
        )

    def test_async_result_erfindet_keinen_kombinator_dazu(self) -> None:
        """Die Kette delegiert - sie entscheidet den Ausgang nicht selbst."""
        ueberzaehlig = sorted(_kombinatoren(AsyncResult) - (_kombinatoren(Ok) | _kombinatoren(Err)))

        assert not ueberzaehlig, (
            f"Diese Kombinatoren gibt es nur auf `AsyncResult`: {ueberzaehlig}. `Ok`/`Err` sind "
            "der einzige Ort, an dem der Ausgang entschieden wird; ein Kombinator ohne "
            "Gegenstueck dort trifft die Entscheidung in der Kette. Nachziehen auf `Ok` und "
            "`Err` in src/contexts/shared_kernel/result.py."
        )


@pytest.mark.asyncio
async def test_zip_legt_einen_fertigen_ausgang_neben_die_kette() -> None:
    """Beleg: `zip` gibt es auch auf der noch nicht erwarteten Form."""
    kette: AsyncResult[int, str] = AsyncResult(_pending(Ok(1)))

    assert await kette.zip(Ok("zwei")) == Ok((1, "zwei"))


@pytest.mark.asyncio
async def test_zip_kuerzt_die_kette_bei_einem_fehler_ab() -> None:
    """Beleg: liegt in der Kette ein Fehler, bleibt er das Ergebnis."""
    kette: AsyncResult[int, str] = AsyncResult(_pending(Err("kaputt")))

    assert await kette.zip(Ok("zwei")) == Err("kaputt")


@pytest.mark.asyncio
async def test_zip_all_legt_einen_fertigen_ausgang_neben_die_kette() -> None:
    """Beleg: `zip_all` gibt es auch auf der noch nicht erwarteten Form."""
    kette: AsyncResult[int, list[str]] = AsyncResult(_pending(Ok(1)))

    assert await kette.zip_all(Ok("zwei")) == Ok((1, "zwei"))


@pytest.mark.asyncio
async def test_zip_all_sammelt_auch_ueber_die_wartende_kette() -> None:
    """Beleg: der Fehler in der Kette und der daneben stehen am Ende nebeneinander."""
    kette: AsyncResult[int, list[str]] = AsyncResult(_pending(Err(["zuerst"])))

    assert await kette.zip_all(Err(["danach"])) == Err(["zuerst", "danach"])
