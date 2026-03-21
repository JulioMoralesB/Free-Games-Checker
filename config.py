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
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Timezone for date display in notifications (e.g. "America/New_York", "Europe/London")
TIMEZONE = os.getenv("TIMEZONE", "UTC")

# Locale for date formatting (e.g. "en_US.UTF-8", "es_ES.UTF-8"). Leave empty to use the system locale.
LOCALE = os.getenv("LOCALE", "")

# Epic Games region used in store links (e.g. "en-US", "es-MX", "de-DE")
EPIC_GAMES_REGION = os.getenv("EPIC_GAMES_REGION", "en-US")

# Daily schedule time in HH:MM format (UTC) at which free games are checked
# NOTE: This is always interpreted as UTC, regardless of the TIMEZONE setting.
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "12:00")

# Health check ping interval in minutes
HEALTHCHECK_INTERVAL = int(os.getenv("HEALTHCHECK_INTERVAL", "1"))

# strftime format string used when displaying the promotion end date in Discord notifications.
# The default is Spanish-style; change to match your locale, e.g. "%B %d, %Y at %I:%M" for en-US.
DATE_FORMAT = os.getenv("DATE_FORMAT", "%d de %B de %Y a las %I:%M")