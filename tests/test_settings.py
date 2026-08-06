"""Tests der Prozess-Konfiguration.

Der Punkt dieser Tests ist die **Startbedingung**: fehlt etwas oder ist es
unbrauchbar, soll der Prozess gar nicht erst hochkommen, statt beim ersten
Zugriff umzufallen.
"""

import pytest

from src.settings import Settings, validate_settings


def test_ohne_passwort_startet_nichts(monkeypatch: pytest.MonkeyPatch) -> None:
    """`DB_PASSWORD` hat bewusst keinen Standardwert."""
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(RuntimeError):
        validate_settings()


def test_ein_unbrauchbarer_port_faellt_beim_start_auf(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ein Port, der keine Zahl ist, ist ein Konfigurationsfehler, kein Laufzeitfehler."""
    monkeypatch.setenv("DB_PASSWORD", "geheim")
    monkeypatch.setenv("DB_PORT", "achtundzwanzig")

    with pytest.raises(RuntimeError):
        validate_settings()


def test_ein_port_ausserhalb_des_bereichs_faellt_auf(monkeypatch: pytest.MonkeyPatch) -> None:
    """65536 ist keine gueltige Portnummer."""
    monkeypatch.setenv("DB_PASSWORD", "geheim")
    monkeypatch.setenv("DB_PORT", "65536")

    with pytest.raises(RuntimeError):
        validate_settings()


def test_die_fehlermeldung_nennt_keinen_wert(monkeypatch: pytest.MonkeyPatch) -> None:
    """Startfehler landen im Log - ein Passwort darf da nicht mitkommen."""
    monkeypatch.setenv("DB_PASSWORD", "streng-geheim")
    monkeypatch.setenv("DB_PORT", "0")

    with pytest.raises(RuntimeError) as raised:
        validate_settings()

    assert "streng-geheim" not in str(raised.value)


def test_die_werte_kommen_aus_der_umgebung(monkeypatch: pytest.MonkeyPatch) -> None:
    """Was gesetzt ist, gewinnt gegen den Standardwert."""
    monkeypatch.setenv("DB_HOST", "datenbank")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_NAME", "eigene_db")
    monkeypatch.setenv("DB_USER", "eigener_nutzer")
    monkeypatch.setenv("DB_PASSWORD", "geheim")

    settings = validate_settings()

    assert settings.db_host == "datenbank"
    assert settings.db_port == 6543
    assert settings.db_name == "eigene_db"
    assert settings.db_user == "eigener_nutzer"


def test_die_url_faehrt_asyncpg_ueber_sqlalchemy() -> None:
    """Ein Weg zur Datenbank - der Dialekt entscheidet, welcher Treiber das ist."""
    settings = Settings(
        db_host="datenbank",
        db_port=6543,
        db_name="eigene_db",
        db_user="eigener_nutzer",
        db_password="geheim",
    )

    assert settings.database_url.render_as_string(hide_password=False) == (
        "postgresql+asyncpg://eigener_nutzer:geheim@datenbank:6543/eigene_db"
    )


def test_sonderzeichen_im_passwort_verschieben_die_url_nicht() -> None:
    """Regression: ein `@` im Passwort verschob die Grenze zwischen Zugangsdaten und Host.

    Bei roher Interpolation las der Treiber alles vor dem **letzten** `@` als
    Zugangsdaten - der Prozess verband sich gegen einen Host, den niemand
    konfiguriert hat, oder gar nicht. Geprueft wird deshalb an den
    Bestandteilen, nicht an der zusammengesetzten Zeichenkette: dass die
    Maskierung stimmt, ist Sache von SQLAlchemy, dass nichts verrutscht, unsere.
    """
    boesartig = "p@ss:w/rd#100%"
    settings = Settings(
        db_host="datenbank",
        db_port=5432,
        db_name="eigene_db",
        db_user="nutzer@firma",
        db_password=boesartig,
    )

    url = settings.database_url

    assert url.password == boesartig
    assert url.username == "nutzer@firma"
    assert url.host == "datenbank"
    assert url.port == 5432
    assert url.database == "eigene_db"


def test_die_url_zeigt_das_passwort_nicht(capsys: pytest.CaptureFixture[str]) -> None:
    """`str(url)` maskiert das Passwort - landet die URL in einem Log, geht es nicht mit."""
    settings = Settings(
        db_host="datenbank",
        db_port=5432,
        db_name="eigene_db",
        db_user="nutzer",
        db_password="streng-geheim",
    )

    print(settings.database_url)

    assert "streng-geheim" not in capsys.readouterr().out
