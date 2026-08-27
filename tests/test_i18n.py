"""Tests für i18n Support am HTTP-Rand: RFC7231-Parsing, Template-Rendering, Migrationsnachweis."""

from src.api.i18n import create_resources, get_language_from_header, translate

_RESOURCES = create_resources()


class TestRFC7231LanguageSelection:
    """RFC 7231 Accept-Language-Header-Auswertung."""

    def test_exact_match_de_DE(self) -> None:
        assert get_language_from_header("de-DE") == "de-DE"

    def test_exact_match_en_US(self) -> None:
        assert get_language_from_header("en-US") == "en-US"

    def test_case_insensitive(self) -> None:
        """en-us wird normalisiert zu en-US."""
        assert get_language_from_header("en-us") == "en-US"

    def test_region_fallback_de(self) -> None:
        """de-AT wird auf de-DE abgebildet."""
        assert get_language_from_header("de-AT") == "de-DE"

    def test_region_fallback_en(self) -> None:
        """en-GB wird auf en-US abgebildet."""
        assert get_language_from_header("en-GB") == "en-US"

    def test_language_only(self) -> None:
        """de ohne Region wird auf de-DE abgebildet."""
        assert get_language_from_header("de") == "de-DE"
        assert get_language_from_header("en") == "en-US"

    def test_q_weight_highest_wins(self) -> None:
        assert get_language_from_header("de;q=0.5,en;q=0.9") == "en-US"

    def test_q_weight_equal_first_wins(self) -> None:
        assert get_language_from_header("de;q=0.5,en;q=0.5") == "de-DE"

    def test_q_zero_excluded(self) -> None:
        """q=0 bedeutet ausdrückliche Ablehnung (ignoriert)."""
        assert get_language_from_header("en;q=0,de") == "de-DE"

    def test_unknown_language_defaults_to_de_DE(self) -> None:
        assert get_language_from_header("fr") == "de-DE"

    def test_empty_header_defaults_to_de_DE(self) -> None:
        assert get_language_from_header("") == "de-DE"

    def test_none_header_defaults_to_de_DE(self) -> None:
        assert get_language_from_header(None) == "de-DE"

    def test_malformed_q_ignored(self) -> None:
        assert get_language_from_header("en;q=invalid,de;q=0.5") == "en-US"


class TestTranslationRendering:
    """Template-Rendering mit Parametern."""

    def test_translate_to_german(self) -> None:
        text = translate(
            _RESOURCES, "password-too-short", {"minimum": 10, "actual_length": 5}, "de-DE"
        )
        assert "mindestens" in text.lower()
        assert "10" in text

    def test_translate_to_english(self) -> None:
        text = translate(
            _RESOURCES, "password-too-short", {"minimum": 10, "actual_length": 5}, "en-US"
        )
        assert "at least" in text.lower()
        assert "10" in text

    def test_different_codes_produce_different_texts(self) -> None:
        de1 = translate(_RESOURCES, "email-already-registered", {}, "de-DE")
        de2 = translate(
            _RESOURCES, "password-too-short", {"minimum": 10, "actual_length": 5}, "de-DE"
        )
        assert de1 != de2

    def test_type_and_code_language_independent(self) -> None:
        code_de = translate(_RESOURCES, "email-already-registered", {}, "de-DE")
        code_en = translate(_RESOURCES, "email-already-registered", {}, "en-US")
        assert code_de
        assert code_en
        assert code_de != code_en


class TestMigrationNachweis:
    """Die Sprachdateien decken dieselbe Code-Menge ab.

    Die frueher hier gepflegten Listen einzelner Codes sind entfallen: sie waren eine
    zweite Wahrheit neben den Fehlerfaellen und mussten von Hand nachgezogen werden.
    Was sie pruefen sollten, prueft jetzt `tests/test_i18n_drift.py` abgeleitet aus den
    Unions - inklusive der Faelle, die frueher schlicht vergessen wurden.
    """

    def test_beide_sprachen_decken_dieselben_codes_ab(self) -> None:
        resources = _RESOURCES
        assert resources.codes("de-DE") == resources.codes("en-US")
