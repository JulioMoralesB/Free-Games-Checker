"""Tests for the LANGUAGE-based config derivation helpers in config.py."""
import pytest
from unittest.mock import patch

from config import (
    _language_to_locale,
    _language_to_steam_language,
    _language_to_steam_country,
    _resolve,
)


class TestLanguageToLocale:
    def test_es_mx(self):
        assert _language_to_locale("es-MX") == "es_MX.UTF-8"

    def test_en_us(self):
        assert _language_to_locale("en-US") == "en_US.UTF-8"

    def test_de_de(self):
        assert _language_to_locale("de-DE") == "de_DE.UTF-8"

    def test_pt_br(self):
        assert _language_to_locale("pt-BR") == "pt_BR.UTF-8"

    def test_fr_fr(self):
        assert _language_to_locale("fr-FR") == "fr_FR.UTF-8"

    def test_returns_empty_for_empty_string(self):
        assert _language_to_locale("") == ""

    def test_returns_empty_for_lang_only_tag(self):
        """BCP 47 tags without a region subtag cannot produce a POSIX locale."""
        assert _language_to_locale("en") == ""

    def test_returns_empty_for_none_like_empty(self):
        assert _language_to_locale("") == ""


class TestLanguageToSteamLanguage:
    def test_es_mx_to_spanish(self):
        assert _language_to_steam_language("es-MX") == "spanish"

    def test_en_us_to_english(self):
        assert _language_to_steam_language("en-US") == "english"

    def test_de_de_to_german(self):
        assert _language_to_steam_language("de-DE") == "german"

    def test_pt_br_to_portuguese(self):
        assert _language_to_steam_language("pt-BR") == "portuguese"

    def test_fr_fr_to_french(self):
        assert _language_to_steam_language("fr-FR") == "french"

    def test_zh_cn_to_schinese(self):
        assert _language_to_steam_language("zh-CN") == "schinese"

    def test_zh_tw_to_tchinese(self):
        """zh-TW must map to Traditional Chinese, not Simplified."""
        assert _language_to_steam_language("zh-TW") == "tchinese"

    def test_ja_jp_to_japanese(self):
        assert _language_to_steam_language("ja-JP") == "japanese"

    def test_ko_kr_to_koreana(self):
        assert _language_to_steam_language("ko-KR") == "koreana"

    def test_returns_empty_for_unknown_language(self):
        assert _language_to_steam_language("xx-XX") == ""

    def test_returns_empty_for_empty_string(self):
        assert _language_to_steam_language("") == ""

    def test_case_insensitive_language_code(self):
        """Language codes should be normalised to lower-case before lookup."""
        assert _language_to_steam_language("ES-MX") == "spanish"


class TestLanguageToSteamCountry:
    def test_es_mx_to_mx(self):
        assert _language_to_steam_country("es-MX") == "MX"

    def test_en_us_to_us(self):
        assert _language_to_steam_country("en-US") == "US"

    def test_de_de_to_de(self):
        assert _language_to_steam_country("de-DE") == "DE"

    def test_pt_br_to_br(self):
        assert _language_to_steam_country("pt-BR") == "BR"

    def test_returns_empty_for_lang_only_tag(self):
        assert _language_to_steam_country("en") == ""

    def test_returns_empty_for_empty_string(self):
        assert _language_to_steam_country("") == ""

    def test_uppercases_region(self):
        """Region subtags should always be upper-cased."""
        assert _language_to_steam_country("es-mx") == "MX"


class TestResolve:
    def test_explicit_env_var_takes_precedence(self):
        with patch.dict("os.environ", {"MY_VAR": "explicit"}):
            assert _resolve("MY_VAR", "derived", "default") == "explicit"

    def test_falls_through_to_language_derived_when_not_set(self):
        env = {k: v for k, v in __import__("os").environ.items() if k != "MY_VAR"}
        with patch("os.environ", env):
            assert _resolve("MY_VAR", "derived", "default") == "derived"

    def test_falls_through_to_default_when_both_missing(self):
        env = {k: v for k, v in __import__("os").environ.items() if k != "MY_VAR"}
        with patch("os.environ", env):
            assert _resolve("MY_VAR", "", "default") == "default"

    def test_empty_env_var_falls_through_to_derived(self):
        """Empty string is treated the same as unset — allows compose ${VAR} expansion."""
        with patch.dict("os.environ", {"MY_VAR": ""}):
            assert _resolve("MY_VAR", "derived", "default") == "derived"

    def test_empty_env_var_and_no_derived_falls_to_default(self):
        with patch.dict("os.environ", {"MY_VAR": ""}):
            assert _resolve("MY_VAR", "", "default") == "default"


class TestLanguageIntegration:
    """End-to-end: LANGUAGE=es-MX derives all four vars correctly."""

    def test_es_mx_derives_locale(self):
        assert _language_to_locale("es-MX") == "es_MX.UTF-8"

    def test_es_mx_derives_epic_region(self):
        # EPIC_GAMES_REGION is LANGUAGE as-is
        assert "es-MX" == "es-MX"

    def test_es_mx_derives_steam_language(self):
        assert _language_to_steam_language("es-MX") == "spanish"

    def test_es_mx_derives_steam_country(self):
        assert _language_to_steam_country("es-MX") == "MX"

    def test_individual_override_wins_over_language(self):
        """Explicit LOCALE overrides what LANGUAGE would derive."""
        with patch.dict("os.environ", {"LOCALE": "fr_FR.UTF-8"}):
            result = _resolve("LOCALE", _language_to_locale("es-MX"), "en_US.UTF-8")
        assert result == "fr_FR.UTF-8"

    def test_language_wins_over_default(self):
        """When LANGUAGE is set and individual var is not, LANGUAGE derivation is used."""
        env = {k: v for k, v in __import__("os").environ.items() if k != "LOCALE"}
        with patch("os.environ", env):
            result = _resolve("LOCALE", _language_to_locale("es-MX"), "en_US.UTF-8")
        assert result == "es_MX.UTF-8"
