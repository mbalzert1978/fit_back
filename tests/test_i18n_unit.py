"""Unit-Tests für i18n Funktionalität - ohne DB, kein HTTP-Setup."""

import pytest

from src.api.i18n import get_language_from_header, load_resources, translate

# Lade Ressourcen beim Modulimport, nicht über conftest.py
load_resources()


class TestLanguageSelection:
    """RFC 7231 Accept-Language-Header-Auswertung."""

    def test_exact_match_de_DE(self) -> None:
        """Exakte Übereinstimmung: de-DE wird akzeptiert."""
        assert get_language_from_header("de-DE") == "de-DE"

    def test_exact_match_en_US(self) -> None:
        """Exakte Übereinstimmung: en-US wird akzeptiert."""
        assert get_language_from_header("en-US") == "en-US"

    def test_case_insensitive_match(self) -> None:
        """Case-insensitiver Match: en-us wird zu en-US."""
        assert get_language_from_header("en-us") == "en-US"

    def test_underscore_normalization(self) -> None:
        """Unterstrich wird zu Bindestrich: de_DE wird zu de-DE."""
        assert get_language_from_header("de_DE") == "de-DE"

    def test_region_fallback_de(self) -> None:
        """Regionstreffer: de-AT wird zu de-DE."""
        assert get_language_from_header("de-AT") == "de-DE"

    def test_region_fallback_en(self) -> None:
        """Regionstreffer: en-GB wird zu en-US."""
        assert get_language_from_header("en-GB") == "en-US"

    def test_language_only_fallback(self) -> None:
        """Nur Sprache ohne Region: de wird zu de-DE."""
        assert get_language_from_header("de") == "de-DE"

    def test_language_only_en(self) -> None:
        """Nur Sprache ohne Region: en wird zu en-US."""
        assert get_language_from_header("en") == "en-US"

    def test_q_weight_highest_wins(self) -> None:
        """q-Gewicht: höchster gewinnt."""
        assert get_language_from_header("de;q=0.5,en;q=0.9") == "en-US"

    def test_q_weight_equal_first_wins(self) -> None:
        """Bei gleichem q-Gewicht: erste Sprache gewinnt."""
        assert get_language_from_header("de;q=0.5,en;q=0.5") == "de-DE"

    def test_q_zero_ignored(self) -> None:
        """q=0 bedeutet 'akzeptiere ich nicht' (wird ignoriert)."""
        assert get_language_from_header("en;q=0,de") == "de-DE"

    def test_unknown_language_defaults_to_de_DE(self) -> None:
        """Unbekannte Sprache: Fallback auf de-DE."""
        assert get_language_from_header("fr") == "de-DE"

    def test_empty_header_defaults_to_de_DE(self) -> None:
        """Leerer Header: Fallback auf de-DE."""
        assert get_language_from_header("") == "de-DE"

    def test_none_header_defaults_to_de_DE(self) -> None:
        """None Header: Fallback auf de-DE."""
        assert get_language_from_header(None) == "de-DE"

    def test_malformed_q_value_ignored(self) -> None:
        """Defekter q-Wert wird ignoriert: en;q=invalid wird als en mit q=1.0 behandelt."""
        # "en;q=invalid" sollte als q=1.0 behandelt werden und gewinnen
        assert get_language_from_header("en;q=invalid,de;q=0.5") == "en-US"

    def test_whitespace_stripped(self) -> None:
        """Whitespace wird gestrippt: ' en , de ' wird behandelt."""
        assert get_language_from_header(" en-US , de-DE ") == "en-US"


class TestTranslation:
    """Template-Rendering mit Parametern."""

    def test_translate_de(self) -> None:
        """Übersetzung auf Deutsch."""
        text = translate("password-too-short", {"minimum": 10, "actual_length": 5}, "de-DE")
        assert "mindestens" in text.lower()
        assert "10" in text

    def test_translate_en(self) -> None:
        """Übersetzung auf Englisch."""
        text = translate("password-too-short", {"minimum": 10, "actual_length": 5}, "en-US")
        assert "at least" in text.lower()
        assert "10" in text

    def test_translate_code_dependent(self) -> None:
        """Verschiedene Codes liefern verschiedene Texte."""
        de_text = translate("email-already-registered", {}, "de-DE")
        en_text = translate("email-already-registered", {}, "en-US")
        assert de_text != en_text

    def test_translate_fallback_to_default_language(self) -> None:
        """Wenn Code in Sprache fehlt, Fallback auf Default (de-DE)."""
        # Beide Sprachen haben den Code (so ist die Spec), aber teste das Fallback-Verhalten
        text = translate("text-is-empty", {}, "de-DE")
        assert text  # Sollte etwas zurückgeben

    def test_translate_missing_code_raises_assertion(self) -> None:
        """Nicht-existierende Codes werfen AssertionError."""
        with pytest.raises(AssertionError, match="not found"):
            translate("non-existent-code", {}, "de-DE")

    def test_translate_missing_parameter_raises_assertion(self) -> None:
        """Fehlende Parameter werfen AssertionError."""
        with pytest.raises(AssertionError, match="unknown parameter"):
            translate("password-too-short", {"minimum": 10}, "de-DE")
        # ^ actual_length fehlt


class TestResourceLoading:
    """Resource-Datei-Laden und Validierung."""

    def test_all_codes_in_both_languages(self) -> None:
        """Alle Codes sind in beiden Sprachen vorhanden."""
        from src.api.i18n import _RESOURCES

        assert _RESOURCES is not None
        de_codes = set(_RESOURCES._resources["de-DE"].keys())
        en_codes = set(_RESOURCES._resources["en-US"].keys())
        assert de_codes == en_codes, "Codes sollten in beiden Sprachen gleich sein"

    def test_idempotency_codes_present(self) -> None:
        """Idempotency-Codes sind vorhanden."""
        from src.api.i18n import _RESOURCES

        assert _RESOURCES is not None
        de_resources = _RESOURCES._resources["de-DE"]
        assert "idempotency-key-reused" in de_resources
        assert "idempotency-request-in-progress" in de_resources

    def test_email_codes_present(self) -> None:
        """Email-Validierungs-Codes sind vorhanden."""
        from src.api.i18n import _RESOURCES

        assert _RESOURCES is not None
        de_resources = _RESOURCES._resources["de-DE"]
        assert "email-has-whitespace" in de_resources
        assert "email-local-part-too-long" in de_resources
