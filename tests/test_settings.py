"""Tests der Prozess-Konfiguration.

Der Punkt dieser Tests ist die **Startbedingung**: fehlt etwas oder ist es
unbrauchbar, soll der Prozess gar nicht erst hochkommen, statt beim ersten
Zugriff umzufallen.

Geprueft wird ueber `get_settings()` - den einzigen oeffentlichen Einstieg in
die Konfiguration. Dass jeder Test dabei die Umgebung frisch liest, besorgt die
autouse-Fixture `_frische_settings` in `tests/conftest.py`; sie leert den Cache
um jeden Test herum.
"""

import pytest

from src.settings import (
    DEFAULT_API_VERSION,
    JWT_SECRET_MINIMUM_LENGTH,
    Settings,
    get_api_version,
    get_settings,
)

GUELTIGES_GEHEIMNIS = "g" * JWT_SECRET_MINIMUM_LENGTH
"""Ein Signaturgeheimnis, das lang genug ist - die Tests hier pruefen anderes."""


def test_ohne_passwort_startet_nichts(monkeypatch: pytest.MonkeyPatch) -> None:
    """`DB_PASSWORD` hat bewusst keinen Standardwert."""
    monkeypatch.setenv("JWT_SECRET", GUELTIGES_GEHEIMNIS)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(RuntimeError):
        get_settings()


def test_ohne_signaturgeheimnis_startet_nichts(monkeypatch: pytest.MonkeyPatch) -> None:
    """`JWT_SECRET` hat bewusst keinen Standardwert.

    Ein Default waere hier eine Hintertuer: wer ihn kennt, signiert sich einen
    Access-Token fuer jedes Konto.
    """
    monkeypatch.setenv("DB_PASSWORD", "geheim")
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(RuntimeError):
        get_settings()


def test_ein_zu_kurzes_signaturgeheimnis_faellt_beim_start_auf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RFC 7518 Abschnitt 3.2: der HMAC-Schluessel ist mindestens so lang wie der Hash.

    `pyjwt` nimmt ein kuerzeres an und warnt nur - eine Warnung im Log haelt
    niemanden auf.
    """
    monkeypatch.setenv("DB_PASSWORD", "geheim")
    monkeypatch.setenv("JWT_SECRET", "g" * (JWT_SECRET_MINIMUM_LENGTH - 1))

    with pytest.raises(RuntimeError):
        get_settings()


def test_das_signaturgeheimnis_taucht_in_keiner_darstellung_auf() -> None:
    """`repr(settings)` landet in Logs und Tracebacks - das Geheimnis darf nicht mit."""
    settings = Settings(db_password="geheim", jwt_secret="s" * JWT_SECRET_MINIMUM_LENGTH)

    assert "s" * JWT_SECRET_MINIMUM_LENGTH not in repr(settings)


def test_ein_unbrauchbarer_port_faellt_beim_start_auf(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ein Port, der keine Zahl ist, ist ein Konfigurationsfehler, kein Laufzeitfehler."""
    monkeypatch.setenv("DB_PASSWORD", "geheim")
    monkeypatch.setenv("JWT_SECRET", GUELTIGES_GEHEIMNIS)
    monkeypatch.setenv("DB_PORT", "achtundzwanzig")

    with pytest.raises(RuntimeError):
        get_settings()


def test_ein_port_ausserhalb_des_bereichs_faellt_auf(monkeypatch: pytest.MonkeyPatch) -> None:
    """65536 ist keine gueltige Portnummer."""
    monkeypatch.setenv("DB_PASSWORD", "geheim")
    monkeypatch.setenv("JWT_SECRET", GUELTIGES_GEHEIMNIS)
    monkeypatch.setenv("DB_PORT", "65536")

    with pytest.raises(RuntimeError):
        get_settings()


def test_die_fehlermeldung_nennt_keinen_wert(monkeypatch: pytest.MonkeyPatch) -> None:
    """Startfehler landen im Log - ein Passwort darf da nicht mitkommen."""
    monkeypatch.setenv("DB_PASSWORD", "streng-geheim")
    monkeypatch.setenv("JWT_SECRET", GUELTIGES_GEHEIMNIS)
    monkeypatch.setenv("DB_PORT", "0")

    with pytest.raises(RuntimeError) as raised:
        get_settings()

    assert "streng-geheim" not in str(raised.value)


def test_die_werte_kommen_aus_der_umgebung(monkeypatch: pytest.MonkeyPatch) -> None:
    """Was gesetzt ist, gewinnt gegen den Standardwert."""
    monkeypatch.setenv("DB_HOST", "datenbank")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_NAME", "eigene_db")
    monkeypatch.setenv("DB_USER", "eigener_nutzer")
    monkeypatch.setenv("DB_PASSWORD", "geheim")
    monkeypatch.setenv("JWT_SECRET", GUELTIGES_GEHEIMNIS)

    settings = get_settings()

    assert settings.db_host == "datenbank"
    assert settings.db_port == 6543
    assert settings.db_name == "eigene_db"
    assert settings.db_user == "eigener_nutzer"


def test_die_api_version_kommt_aus_der_umgebung(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ohne `API_VERSION` gilt der Default, mit ihr gewinnt sie."""
    monkeypatch.delenv("API_VERSION", raising=False)
    assert get_api_version() == DEFAULT_API_VERSION

    get_api_version.cache_clear()
    monkeypatch.setenv("API_VERSION", "7")

    assert get_api_version() == "7"


def test_die_api_version_braucht_keine_vollstaendige_umgebung(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Der Einstiegspunkt liest sie beim Import - da gibt es noch kein DB-Passwort.

    Deshalb hat sie einen eigenen Weg herein und laeuft nicht ueber
    `get_settings`, das ohne `DB_PASSWORD` und `JWT_SECRET` scheitert.
    """
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)

    assert get_api_version() == DEFAULT_API_VERSION


def test_die_url_faehrt_asyncpg_ueber_sqlalchemy() -> None:
    """Ein Weg zur Datenbank - der Dialekt entscheidet, welcher Treiber das ist."""
    settings = Settings(
        db_host="datenbank",
        db_port=6543,
        db_name="eigene_db",
        db_user="eigener_nutzer",
        db_password="geheim",
        jwt_secret=GUELTIGES_GEHEIMNIS,
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
        jwt_secret=GUELTIGES_GEHEIMNIS,
    )

    url = settings.database_url

    assert url.password == boesartig
    assert url.username == "nutzer@firma"
    assert url.host == "datenbank"
    assert url.port == 5432
    assert url.database == "eigene_db"


def test_die_url_zeigt_das_passwort_nicht() -> None:
    """`str(url)` maskiert das Passwort - landet die URL in einem Log, geht es nicht mit."""
    settings = Settings(
        db_host="datenbank",
        db_port=5432,
        db_name="eigene_db",
        db_user="nutzer",
        db_password="streng-geheim",
        jwt_secret=GUELTIGES_GEHEIMNIS,
    )

    assert "streng-geheim" not in str(settings.database_url)
