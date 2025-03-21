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
            gameId = ""
            try:
                offerPageSlug = game["offerMappings"][0]["pageSlug"]
                if offerPageSlug:
                    logger.info(f"Found Offer Page Slug: {offerPageSlug}")
                    gameId = offerPageSlug
            except IndexError:
                logger.info("No Offer Page Slug found.")
                try:
                    pageSlug = game["catalogNs"]["mappings"][0]["pageSlug"]
                    if pageSlug:
                        logger.info(f"Found CatalogNs Page Slug: {pageSlug}")
                        gameId = pageSlug
                except IndexError:
                    logger.info("No CatalogNs Page Slug found.")
            if gameId:
                logger.info(f"Using gameId: {gameId}")
                link = f"https://store.epicgames.com/es-MX/p/{gameId}"
            else:
                logger.info("No game url found, using default link.")
                link = "https://store.epicgames.com/es-MX/free-games"    
                
            end_date = ""
            logger.info(f"Promotions: {game['promotions']}")
            for offer in game["promotions"]["promotionalOffers"][0]["promotionalOffers"]:
                if offer["discountSetting"]["discountPercentage"] == 0:
                    end_date = offer["endDate"]
                    break
            logger.info(f"End Date: {end_date}")

            description = game["description"]
            logger.info(f"Description: {description}")

            for image in game["keyImages"]:
                if image["type"] == "Thumbnail":
                    thumbnail = image["url"]
                    break
            logger.info(f"Thumbnail: {thumbnail}")

            games.append({"title": title, "link": link, "endDate": end_date, "description": description, "thumbnail": thumbnail})
    logger.info(f"Returning games: {games}")
    return games