"""Epic Games Store scraper implementation."""

import json
import re
import unicodedata
import requests
import logging
from config import EPIC_GAMES_API_URL, EPIC_GAMES_REGION
from modules.models import FreeGame
from modules.retry import with_retry
from modules.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_RETRYABLE_ERRORS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
)

_METACRITIC_BASE = "https://www.metacritic.com/game"

# Mimic a browser so Metacritic serves the full HTML page with JSON-LD structured data.
_MC_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def make_metacritic_slug(title: str) -> str:
    """Convert a game title to a Metacritic URL slug.

    Examples
    --------
    >>> make_metacritic_slug("The Witcher 3: Wild Hunt")
    'the-witcher-3-wild-hunt'
    >>> make_metacritic_slug("Baldur's Gate 3")
    'baldurs-gate-3'
    """
    # Strip accents → ASCII
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = ascii_title.lower()
    # Remove characters that are not word chars, spaces, or hyphens
    slug = re.sub(r"[^\w\s-]", "", slug)
    # Replace whitespace / underscores with a single hyphen
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    # Collapse consecutive hyphens
    slug = re.sub(r"-+", "-", slug)
    return slug


class EpicGamesScraper(BaseScraper):
    """Scraper for Epic Games Store free game promotions."""

    @property
    def store_name(self) -> str:
        """Store name identifier."""
        return "epic"

    def fetch_free_games(self) -> list[FreeGame]:
        """Fetch free games from Epic Games API.
        
        Returns
        -------
        list[FreeGame]
            List of free games currently available on Epic Games Store.
        """
        logger.info(f"Fetching free games from Epic Games API. URI: {EPIC_GAMES_API_URL}")
        try:
            response = with_retry(
                func=lambda: requests.get(EPIC_GAMES_API_URL, timeout=10),
                max_attempts=4,
                base_delay=1,
                retryable_exceptions=_RETRYABLE_ERRORS,
                description="Epic Games API fetch",
            )
        except _RETRYABLE_ERRORS as e:
            logger.error("Failed to fetch Epic Games API after retries: %s", e, exc_info=True)
            return []

        if response.status_code != 200:
            logger.error(f"Failed to fetch Epic Games API. Status Code: {response.status_code}")
            return []
        
        data = response.json()
        logger.info(f"Response obtained from Epic Games API. Response Keys: {list(data.keys())}")
        games = []

        for game in data["data"]["Catalog"]["searchStore"]["elements"]:
            price_info = game.get("price", {}).get("totalPrice", {})
            if price_info.get("discountPrice", 1) == 0:
                original_price_int = price_info.get("originalPrice", 0)
                if original_price_int > 0:
                    fmt = price_info.get("fmtPrice", {})
                    original_price = fmt.get("originalPrice") or None
                    if original_price == "0":
                        original_price = None
                else:
                    original_price = None
                ## Get the game title
                title = game["title"]
                logger.info(f"Found free game!: {title}")
                
                ## Get the game link
                game_id = ""
                ## If the game is a mystery game, skip it
                if "Mystery Game" in title:
                    logger.info("Mystery Game found, skipping.")
                    continue
                
                ## Try to get the offer page slug
                try:
                    offer_page_slug = game["offerMappings"][0]["pageSlug"]
                    if offer_page_slug:
                        logger.info(f"Found Offer Page Slug: {offer_page_slug}")
                        game_id = offer_page_slug
                
                except IndexError:
                    logger.info("No Offer Page Slug found.")
                ## If it fails, try to get the catalogNs page slug
                if not game_id:
                    try:
                        page_slug = game["catalogNs"]["mappings"][0]["pageSlug"]
                        if page_slug:
                            logger.info(f"Found CatalogNs Page Slug: {page_slug}")
                            game_id = page_slug
                    except IndexError:
                        logger.info("No CatalogNs Page Slug found.")
                ## If it fails, try to get the product slug
                if not game_id:
                    try:
                        product_slug = game["productSlug"]
                        if product_slug:
                            logger.info(f"Found Product Slug: {product_slug}")
                            game_id = product_slug
                    except KeyError:
                        logger.info("No Product Slug found.")
                
                ## If game_id is found, use it to create the link
                if game_id:
                    logger.info(f"Using game_id: {game_id}")
                    link = f"https://store.epicgames.com/{EPIC_GAMES_REGION}/p/{game_id}"
                ## If not, use the default link
                else:
                    logger.info("No game url found, using default link.")
                    link = f"https://store.epicgames.com/{EPIC_GAMES_REGION}/free-games"
                    
                end_date = ""
                promotions = game.get("promotions")
                logger.debug(f"Promotions payload: {promotions}")
                logger.info(f"Promotions present: {bool(promotions)}")
                #If there are no promotional offers, skip the game
                if not promotions or not promotions.get("promotionalOffers"):
                    logger.info("No promotional offers found, skipping.")
                    continue
                for offer in promotions["promotionalOffers"][0]["promotionalOffers"]:
                    if offer["discountSetting"]["discountPercentage"] == 0:
                        end_date = offer["endDate"]
                        break
                logger.info(f"Computed end_date: {end_date}")

                description = game["description"]
                logger.info(f"Description: {description}")
                logger.info("Trying to find thumbnail.")
                thumbnail = "" 
                for image in game["keyImages"]:
                    if image["type"] == "Thumbnail":
                        thumbnail = image["url"]
                        logger.info(f"Found Thumbnail: {thumbnail}")
                        break
                if not thumbnail:
                    logger.info("No Thumbnail found, trying a different image.")
                    thumbnail = game["keyImages"][0]["url"]
                if not thumbnail:
                    logger.info("No image found, using default.")
                    thumbnail = "https://static-assets-prod.epicgames.com/epic-store/static/webpack/25c285e020572b4f76b770d6cca272ec.png"
                logger.info(f"Thumbnail to be used: {thumbnail}")

                review_score = self._fetch_metacritic_score(title)

                games.append(
                    FreeGame(
                        title=title,
                        store=self.store_name,
                        url=link,
                        image_url=thumbnail,
                        original_price=original_price,
                        end_date=end_date,
                        is_permanent=False,
                        description=description,
                        game_type="game",
                        review_score=review_score,
                    )
                )
        logger.info(f"Returning {len(games)} games")
        logger.debug(f"Returning game titles: {[game.title for game in games]}")
        return games

    def _fetch_metacritic_score(self, title: str) -> str | None:
        """Return a Metascore string like ``"Metascore: 83"`` for *title*, or None.

        Metacritic embeds critic-score data as JSON-LD structured data
        (``<script type="application/ld+json">``) on each game page, so no API
        key is required.  Any network or parsing failure is logged as a warning
        and returns None so a single game's lookup never blocks the whole scrape.
        """
        slug = make_metacritic_slug(title)
        url = f"{_METACRITIC_BASE}/{slug}/"
        logger.info("Metacritic: fetching score for %r → %s", title, url)

        try:
            resp = requests.get(url, headers=_MC_HEADERS, timeout=10)
            if resp.status_code != 200:
                logger.info(
                    "Metacritic: HTTP %s for %r — skipping review score",
                    resp.status_code, title,
                )
                return None

            # Extract every JSON-LD block from the page HTML
            blocks = re.findall(
                r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
                resp.text,
                re.DOTALL,
            )
            for raw_block in blocks:
                try:
                    data = json.loads(raw_block)
                except json.JSONDecodeError:
                    continue

                agg = data.get("aggregateRating") or {}
                value = agg.get("ratingValue")
                if value is not None:
                    try:
                        score = int(value)
                        logger.info("Metacritic: %r → Metascore %d", title, score)
                        return f"Metascore: {score}"
                    except (ValueError, TypeError):
                        continue

            logger.info("Metacritic: no aggregateRating found for %r", title)

        except Exception as exc:
            logger.warning("Metacritic: failed to fetch score for %r: %s", title, exc)

        return None
