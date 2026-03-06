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
ENABLE_HEALTHCHECK = os.getenv("ENABLE_HEALTHCHECK").lower() == "true"

# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")