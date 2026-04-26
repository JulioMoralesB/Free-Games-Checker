import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Epic Games API URL
EPIC_GAMES_API_URL = os.getenv("EPIC_GAMES_API_URL", "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions")

# Comma-separated list of store identifiers to fetch free games from (e.g. "epic,steam").
# Defaults to "epic" for backwards compatibility. Unknown stores are ignored with a warning.
_raw_enabled_stores = os.getenv("ENABLED_STORES", "epic")
ENABLED_STORES = [s.strip().lower() for s in _raw_enabled_stores.split(",") if s.strip()]

# Steam Store search URL
STEAM_SEARCH_URL = os.getenv("STEAM_SEARCH_URL", "https://store.steampowered.com/search/")

# ─────────────────────────────────────────────────────────────────────────────
# Unified language / region config
#
# Set LANGUAGE to a BCP 47 tag (e.g. "es-MX", "de-DE", "pt-BR") and the app
# derives LOCALE, EPIC_GAMES_REGION, STEAM_LANGUAGE, STEAM_COUNTRY, and
# TIMEZONE automatically.  Any of those five vars can still be set
# individually to override the derived value (individual var always wins).
# ─────────────────────────────────────────────────────────────────────────────
LANGUAGE = os.getenv("LANGUAGE", "")

# ISO 639-1 code → Steam API language name.
# Reference: https://partner.steamgames.com/doc/store/localization/languages
_STEAM_LANGUAGE_MAP: dict[str, str] = {
    "af": "afrikaans",
    "ar": "arabic",
    "bg": "bulgarian",
    "cs": "czech",
    "da": "danish",
    "de": "german",
    "el": "greek",
    "en": "english",
    "es": "spanish",
    "fi": "finnish",
    "fr": "french",
    "hu": "hungarian",
    "it": "italian",
    "ja": "japanese",
    "ko": "koreana",
    "nl": "dutch",
    "no": "norwegian",
    "pl": "polish",
    "pt": "portuguese",
    "ro": "romanian",
    "ru": "russian",
    "sv": "swedish",
    "th": "thai",
    "tr": "turkish",
    "uk": "ukrainian",
    "vi": "vietnamese",
    "zh": "schinese",  # default Simplified; zh-TW handled in _language_to_steam_language
}


def _language_to_locale(language: str) -> str:
    """Map BCP 47 tag to POSIX locale: 'es-MX' → 'es_MX.UTF-8'. Returns '' if unresolvable."""
    if not language or "-" not in language:
        return ""
    lang, region = language.split("-", 1)
    return f"{lang}_{region}.UTF-8"


def _language_to_steam_language(language: str) -> str:
    """Map BCP 47 tag to Steam language name: 'es-MX' → 'spanish'. Returns '' when unknown."""
    if not language:
        return ""
    parts = language.split("-", 1)
    lang_code = parts[0].lower()
    region = parts[1].upper() if len(parts) > 1 else ""
    if lang_code == "zh" and region == "TW":
        return "tchinese"
    return _STEAM_LANGUAGE_MAP.get(lang_code, "")


def _language_to_steam_country(language: str) -> str:
    """Extract ISO country code from BCP 47 tag: 'es-MX' → 'MX'. Returns '' when absent."""
    if not language or "-" not in language:
        return ""
    return language.split("-", 1)[1].upper()


# ISO 3166-1 alpha-2 country code → representative IANA timezone.
# For countries with multiple timezones the most-populated zone is used.
_TIMEZONE_MAP: dict[str, str] = {
    # Americas
    "AR": "America/Argentina/Buenos_Aires",
    "BO": "America/La_Paz",
    "BR": "America/Sao_Paulo",
    "CA": "America/Toronto",
    "CL": "America/Santiago",
    "CO": "America/Bogota",
    "CR": "America/Costa_Rica",
    "CU": "America/Havana",
    "DO": "America/Santo_Domingo",
    "EC": "America/Guayaquil",
    "GT": "America/Guatemala",
    "HN": "America/Tegucigalpa",
    "MX": "America/Mexico_City",
    "NI": "America/Managua",
    "PA": "America/Panama",
    "PE": "America/Lima",
    "PR": "America/Puerto_Rico",
    "PY": "America/Asuncion",
    "SV": "America/El_Salvador",
    "US": "America/New_York",
    "UY": "America/Montevideo",
    "VE": "America/Caracas",
    # Europe
    "AT": "Europe/Vienna",
    "BE": "Europe/Brussels",
    "BG": "Europe/Sofia",
    "BY": "Europe/Minsk",
    "CH": "Europe/Zurich",
    "CZ": "Europe/Prague",
    "DE": "Europe/Berlin",
    "DK": "Europe/Copenhagen",
    "EE": "Europe/Tallinn",
    "ES": "Europe/Madrid",
    "FI": "Europe/Helsinki",
    "FR": "Europe/Paris",
    "GB": "Europe/London",
    "GR": "Europe/Athens",
    "HR": "Europe/Zagreb",
    "HU": "Europe/Budapest",
    "IE": "Europe/Dublin",
    "IT": "Europe/Rome",
    "LT": "Europe/Vilnius",
    "LV": "Europe/Riga",
    "NL": "Europe/Amsterdam",
    "NO": "Europe/Oslo",
    "PL": "Europe/Warsaw",
    "PT": "Europe/Lisbon",
    "RO": "Europe/Bucharest",
    "RS": "Europe/Belgrade",
    "RU": "Europe/Moscow",
    "SE": "Europe/Stockholm",
    "SI": "Europe/Ljubljana",
    "SK": "Europe/Bratislava",
    "TR": "Europe/Istanbul",
    "UA": "Europe/Kyiv",
    # Asia / Pacific
    "AE": "Asia/Dubai",
    "AF": "Asia/Kabul",
    "AU": "Australia/Sydney",
    "CN": "Asia/Shanghai",
    "HK": "Asia/Hong_Kong",
    "ID": "Asia/Jakarta",
    "IL": "Asia/Jerusalem",
    "IN": "Asia/Kolkata",
    "IQ": "Asia/Baghdad",
    "IR": "Asia/Tehran",
    "JP": "Asia/Tokyo",
    "KR": "Asia/Seoul",
    "KZ": "Asia/Almaty",
    "MY": "Asia/Kuala_Lumpur",
    "NZ": "Pacific/Auckland",
    "PH": "Asia/Manila",
    "PK": "Asia/Karachi",
    "SA": "Asia/Riyadh",
    "SG": "Asia/Singapore",
    "TH": "Asia/Bangkok",
    "TW": "Asia/Taipei",
    "UA": "Europe/Kyiv",
    "VN": "Asia/Ho_Chi_Minh",
    # Africa
    "DZ": "Africa/Algiers",
    "EG": "Africa/Cairo",
    "ET": "Africa/Addis_Ababa",
    "GH": "Africa/Accra",
    "KE": "Africa/Nairobi",
    "MA": "Africa/Casablanca",
    "NG": "Africa/Lagos",
    "TN": "Africa/Tunis",
    "TZ": "Africa/Dar_es_Salaam",
    "ZA": "Africa/Johannesburg",
}


def _language_to_timezone(language: str) -> str:
    """Map BCP 47 country subtag to an IANA timezone: 'es-MX' → 'America/Mexico_City'.

    Returns '' when the country code is absent or not in the map.
    For countries with multiple timezones the most-populated zone is used.
    Use TIMEZONE directly to override with a specific zone.
    """
    if not language or "-" not in language:
        return ""
    country = language.split("-", 1)[1].upper()
    return _TIMEZONE_MAP.get(country, "")


def _resolve(env_var: str, language_derived: str, default: str) -> str:
    """Resolve a config value: explicit env var (non-empty) > LANGUAGE derivation > hardcoded default.

    An empty string is treated the same as "not set", so that compose.yaml can
    forward ``${VAR}`` (which expands to '' when unset) without blocking LANGUAGE
    derivation.  To override with an explicit empty value, set the var directly
    in config — this edge case is not expected in normal usage.
    """
    explicit = os.getenv(env_var)
    if explicit:  # non-None and non-empty
        return explicit
    if language_derived:
        return language_derived
    return default


# Language for Steam appdetails API (e.g. "english", "spanish").
# Derived from LANGUAGE when not set explicitly; falls back to "english".
STEAM_LANGUAGE = _resolve("STEAM_LANGUAGE", _language_to_steam_language(LANGUAGE), "english")

# Country code for Steam store requests — controls price currency (e.g. "US", "MX").
# Derived from LANGUAGE when not set explicitly; falls back to "US".
STEAM_COUNTRY = _resolve("STEAM_COUNTRY", _language_to_steam_country(LANGUAGE), "US")

# Minimum delay in milliseconds between Steam HTTP requests to avoid rate limiting
_raw_steam_delay = os.getenv("STEAM_REQUEST_DELAY_MS")
try:
    STEAM_REQUEST_DELAY_MS = max(0, int(_raw_steam_delay)) if _raw_steam_delay not in (None, "") else 1500
except ValueError:
    STEAM_REQUEST_DELAY_MS = 1500

# Discord Webhook URL (loaded from .env)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Path to store free games data
DATA_FILE_PATH = "/mnt/data/free_games.json" # This path can be overridden by mounting a volume in Docker

# Path to store the last sent notification batch (used by the resend endpoint)
LAST_NOTIFICATION_FILE_PATH = "/mnt/data/last_notification.json"

# URL to Healthcheck Monitor
HEALTHCHECK_URL = os.getenv("HEALTHCHECK_URL")

# Enable or disable healthcheck based on environment variable
ENABLE_HEALTHCHECK = os.getenv("ENABLE_HEALTHCHECK", "false").lower() == "true"

# Database configuration
DB_HOST = os.getenv("DB_HOST") or None
_raw_db_port = os.getenv("DB_PORT")
DB_PORT = int(_raw_db_port) if _raw_db_port and _raw_db_port.strip() else 5432
DB_NAME = os.getenv("DB_NAME") or None
DB_USER = os.getenv("DB_USER") or None
DB_PASSWORD = os.getenv("DB_PASSWORD") or None

# Timezone for date display in notifications (e.g. "America/New_York", "Europe/London").
# Derived from LANGUAGE when not set explicitly; falls back to "UTC".
TIMEZONE = _resolve("TIMEZONE", _language_to_timezone(LANGUAGE), "UTC")

# Locale for date formatting (e.g. "en_US.UTF-8", "es_MX.UTF-8").
# Derived from LANGUAGE when not set explicitly; falls back to "en_US.UTF-8".
LOCALE = _resolve("LOCALE", _language_to_locale(LANGUAGE), "en_US.UTF-8")

# Epic Games region used in store links (e.g. "en-US", "es-MX", "de-DE").
# Defaults to LANGUAGE when not set explicitly; falls back to "en-US".
EPIC_GAMES_REGION = _resolve("EPIC_GAMES_REGION", LANGUAGE, "en-US")

# How often to check for new free games, in hours.
# When set, the service runs on a repeating interval (e.g. every 6 hours).
# When left empty, the service falls back to SCHEDULE_TIME and runs once per day.
# Recommended for multi-store setups (Steam games can appear at any time).
# Minimum value is 1 hour.
_raw_check_interval = os.getenv("CHECK_INTERVAL_HOURS")
try:
    if _raw_check_interval in (None, ""):
        CHECK_INTERVAL_HOURS = None
    else:
        _parsed = float(_raw_check_interval)
        if _parsed < 1:
            logging.warning(
                "CHECK_INTERVAL_HOURS value %r is below the 1-hour minimum; defaulting to 1 hour.",
                _raw_check_interval,
            )
            CHECK_INTERVAL_HOURS = 1.0
        else:
            CHECK_INTERVAL_HOURS = _parsed
except ValueError:
    logging.error(
        "Invalid CHECK_INTERVAL_HOURS value %r (not a number); falling back to SCHEDULE_TIME.",
        _raw_check_interval,
    )
    CHECK_INTERVAL_HOURS = None

# Daily schedule time in HH:MM format at which free games are checked.
# Used only when CHECK_INTERVAL_HOURS is not set.
# NOTE: This time is interpreted in the configured TIMEZONE (see TIMEZONE above), not fixed to UTC.
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "12:00")

# Health check ping interval in minutes
_raw_healthcheck_interval = os.getenv("HEALTHCHECK_INTERVAL")
try:
    if _raw_healthcheck_interval in (None, ""):
        HEALTHCHECK_INTERVAL = 1
    else:
        HEALTHCHECK_INTERVAL = max(1, int(_raw_healthcheck_interval))
except ValueError:
    HEALTHCHECK_INTERVAL = 1

# strftime format string used when displaying the promotion end date in Discord notifications.
# The default is English-style; change to match your locale, e.g. "%d de %B de %Y a las %I:%M %p" for LOCALE="es_ES.UTF-8".
DATE_FORMAT = os.getenv("DATE_FORMAT", "%B %d, %Y at %I:%M %p")

# REST API configuration
API_KEY = os.getenv("API_KEY")  # Secret key for mutating API endpoints; leave empty to disable auth
API_HOST = os.getenv("API_HOST", "0.0.0.0")
_raw_api_port = os.getenv("API_PORT")
try:
    if _raw_api_port in (None, ""):
        API_PORT = 8000
    else:
        _parsed_api_port = int(_raw_api_port)
        if 1 <= _parsed_api_port <= 65535:
            API_PORT = _parsed_api_port
        else:
            logging.error(
                "API_PORT '%s' is out of valid range (1–65535); defaulting to 8000",
                _raw_api_port,
            )
            API_PORT = 8000
except ValueError:
    logging.error(
        "Invalid API_PORT '%s' (not a number); defaulting to 8000",
        _raw_api_port,
    )
    API_PORT = 8000