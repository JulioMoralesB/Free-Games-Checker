import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Epic Games API URL
EPIC_GAMES_API_URL = os.getenv("EPIC_GAMES_API_URL", "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions")

# Discord Webhook URL (loaded from .env)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Path to store free games data
DATA_FILE_PATH = "/mnt/data/free_games.json" # This path can be overridden by mounting a volume in Docker

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

# Daily schedule time in HH:MM format at which free games are checked.
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