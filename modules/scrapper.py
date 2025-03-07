import requests
from config import EPIC_GAMES_API_URL

import logging
logger = logging.getLogger(__name__)

def fetch_free_games():
    """Fetch free games from Epic Games API."""
    logger.info(f"Fetching free games from Epic Games API. URI: {EPIC_GAMES_API_URL}")
    response = requests.get(EPIC_GAMES_API_URL)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch Epic Games API. Status Code: {response.status_code}")
        return []
    
    data = response.json()
    logger.info(f"Response obtained from Epic Games API.")
    games = []

    for game in data["data"]["Catalog"]["searchStore"]["elements"]:
        price_info = game.get("price", {}).get("totalPrice", {})
        if price_info.get("discountPrice", 1) == 0:
            title = game["title"]
            logger.info(f"Found free game!: {title}")
            link = f"https://store.epicgames.com/es-MX/p/{game['urlSlug']}"
            end_date = ""
            for offer in game["promotions"]["promotionalOffers"][0]["promotionalOffers"]:
                if offer["discountSetting"]["discountPercentage"] == 0:
                    end_date = offer["endDate"]
            games.append({"title": title, "link": link, "endDate": end_date})
    logger.info(f"Returning games: {games}")
    return games