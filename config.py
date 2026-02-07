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
DATA_FILE_PATH = "/mnt/data/free_games.json"

# URL to Healthcheck Monitor
HEALTHCHECK_URL = os.getenv("HEALTHCHECK_URL")