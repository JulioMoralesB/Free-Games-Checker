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

# Language passed to the Steam appdetails API for game descriptions.
# Supported values: english, spanish, french, german, portuguese, russian, etc.
# Full list: https://partner.steamgames.com/doc/store/localization/languages
STEAM_LANGUAGE = os.getenv("STEAM_LANGUAGE", "english")

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

# Timezone for date display in notifications (e.g. "America/New_York", "Europe/London")
TIMEZONE = os.getenv("TIMEZONE", "UTC")

# Locale for date formatting (e.g. "en_US.UTF-8", "es_ES.UTF-8"). Defaults to "en_US.UTF-8"; set LOCALE to an empty string to use the system locale.
LOCALE = os.getenv("LOCALE", "en_US.UTF-8")

# Epic Games region used in store links (e.g. "en-US", "es-MX", "de-DE")
EPIC_GAMES_REGION = os.getenv("EPIC_GAMES_REGION", "en-US")

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