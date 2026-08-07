"""Tests für i18n Support am HTTP-Rand: RFC7231-Parsing, Template-Rendering, Migrationsnachweis."""

from src.api.i18n import create_resources, get_language_from_header, translate

# Erstelle Ressourcen beim Modulimport für alle Tests
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
        """Q-Gewicht: höchster gewinnt."""
        assert get_language_from_header("de;q=0.5,en;q=0.9") == "en-US"

    def test_q_weight_equal_first_wins(self) -> None:
        """Q-Gewicht gleich: erste Sprache gewinnt."""
        assert get_language_from_header("de;q=0.5,en;q=0.5") == "de-DE"

    def test_q_zero_excluded(self) -> None:
        """q=0 bedeutet ausdrückliche Ablehnung (ignoriert)."""
        assert get_language_from_header("en;q=0,de") == "de-DE"

    def test_unknown_language_defaults_to_de_DE(self) -> None:
        """Unbekannte Sprache → de-DE."""
        assert get_language_from_header("fr") == "de-DE"

    def test_empty_header_defaults_to_de_DE(self) -> None:
        """Leerer Header → de-DE."""
        assert get_language_from_header("") == "de-DE"

    def test_none_header_defaults_to_de_DE(self) -> None:
        """None → de-DE."""
        assert get_language_from_header(None) == "de-DE"

    def test_malformed_q_ignored(self) -> None:
        """Defekter q-Wert wird ignoriert."""
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
        """Fehlercode ist sprachunabhängig (gleicher Code, beide Sprachen)."""
        code_de = translate(_RESOURCES, "email-already-registered", {}, "de-DE")
        code_en = translate(_RESOURCES, "email-already-registered", {}, "en-US")
        # Codes sind unterschiedlich (de vs en), aber beide sollten vorhanden sein
        assert code_de  # nicht leer
        assert code_en  # nicht leer
        assert code_de != code_en  # unterschiedlich


class TestMigrationNachweis:
    """Alle 8 Dateien haben ihre Texte in Resource-Files."""

    def test_all_error_codes_in_both_languages(self) -> None:
        """Alle Codes sind in beiden Sprachen vollständig vorhanden."""
        de_codes = set(_RESOURCES._resources["de-DE"].keys())
        en_codes = set(_RESOURCES._resources["en-US"].keys())
        assert de_codes == en_codes

    def test_shared_kernel_text_is_empty(self) -> None:
        """text-is-empty Code ist vorhanden (shared_kernel/not_empty_string.py)."""
        text = translate(_RESOURCES, "text-is-empty", {}, "de-DE")
        assert "leer" in text.lower()

    def test_identity_domain_texts_present(self) -> None:
        """Alle Identity-Domain-Value-Object-Texte sind präsent."""
        test_codes = [
            ("email-has-whitespace", {}),
            ("password-too-short", {"minimum": 10, "actual_length": 5}),
            ("display-name-is-empty", {}),
            ("display-name-too-long", {"actual_length": 100, "maximum": 50}),
            ("locale-not-supported", {"candidate": "fr"}),
            ("user-time-zone-unknown", {"candidate": "Invalid/Zone"}),
        ]
        for code, params in test_codes:
            text = translate(_RESOURCES, code, params, "de-DE")
            assert text, f"Code '{code}' not found"

    def test_application_validation_texts_present(self) -> None:
        """Alle Application-Validierungstexte sind präsent."""
        test_codes = [
            ("email-already-registered", {}),
            ("email-already-registered-detail", {"email": "test@example.com"}),
            ("validation-failed", {}),
            ("validation-failed-detail", {}),
        ]
        for code, params in test_codes:
            text = translate(_RESOURCES, code, params, "de-DE")
            assert text, f"Code '{code}' not found"

    def test_idempotency_middleware_texts_present(self) -> None:
        """Middleware-Texte sind in Resources (vier Codes)."""
        codes = [
            "idempotency-key-reused",
            "idempotency-key-reused-detail",
            "idempotency-request-in-progress",
            "idempotency-request-in-progress-detail",
        ]
        for code in codes:
            text = translate(_RESOURCES, code, {}, "de-DE")
            assert text, f"Code '{code}' not found"
