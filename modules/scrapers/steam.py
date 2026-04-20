"""Steam store scraper implementation."""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config import STEAM_SEARCH_URL
from modules.models import FreeGame
from modules.retry import with_retry
from modules.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_RETRYABLE_ERRORS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_SEARCH_PARAMS = {
    "maxprice": "free",
    "specials": 1,
    "cc": "US",
    "l": "english",
}

_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
_APPREVIEWS_URL = "https://store.steampowered.com/appreviews"

_END_DATE_RE = re.compile(
    r"before\s+(\d{1,2})\s+(\w{3})\s+@\s+(\d{1,2}):(\d{2})(am|pm)",
    re.IGNORECASE,
)


def _parse_steam_end_date(text: str) -> str:
    """Parse 'before DD Mon @ HH:MMam/pm' into an ISO-8601 UTC string."""
    m = _END_DATE_RE.search(text)
    if not m:
        return ""
    day, month_str, hour, minute, ampm = m.groups()
    try:
        month = datetime.strptime(month_str, "%b").month
        hour = int(hour)
        if ampm.lower() == "pm" and hour != 12:
            hour += 12
        elif ampm.lower() == "am" and hour == 12:
            hour = 0
        now = datetime.now(tz=timezone.utc)
        dt = datetime(now.year, month, int(day), hour, int(minute), tzinfo=timezone.utc)
        if dt < now:
            dt = dt.replace(year=now.year + 1)
        return dt.isoformat()
    except ValueError:
        return ""


class SteamScraper(BaseScraper):
    """Scraper for Steam free game promotions."""

    @property
    def store_name(self) -> str:
        return "steam"

    def fetch_free_games(self) -> list[FreeGame]:
        logger.info("Fetching free games from Steam. URL: %s", STEAM_SEARCH_URL)
        try:
            response = with_retry(
                func=lambda: requests.get(
                    STEAM_SEARCH_URL,
                    params=_SEARCH_PARAMS,
                    headers=_HEADERS,
                    timeout=10,
                ),
                max_attempts=4,
                base_delay=1,
                retryable_exceptions=_RETRYABLE_ERRORS,
                description="Steam search fetch",
            )
        except _RETRYABLE_ERRORS as e:
            logger.error("Failed to fetch Steam search after retries: %s", e, exc_info=True)
            return []

        if response.status_code != 200:
            logger.error("Failed to fetch Steam search. Status: %s", response.status_code)
            return []

        candidates = self._parse_search_page(response.text)
        logger.info("Found %d free game candidates.", len(candidates))

        games = [self._build_game(c) for c in candidates]
        logger.info("Returning %d Steam free games.", len(games))
        return games

    def _parse_search_page(self, html: str) -> list[dict]:
        """Return candidate dicts for games with price_final==0 and an original price."""
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("#search_resultsRows a.search_result_row")
        logger.info("Steam search returned %d result rows.", len(rows))

        candidates = []
        for row in rows:
            price_div = row.select_one("[data-price-final]")
            if not price_div:
                continue
            try:
                price_final = int(price_div.get("data-price-final", 1))
            except (ValueError, TypeError):
                continue

            original_el = row.select_one(".discount_original_price")
            if price_final != 0 or not original_el:
                continue

            appid = row.get("data-ds-appid", "")
            title_el = row.select_one(".title")
            candidates.append({
                "appid": appid,
                "title": title_el.text.strip() if title_el else "",
                "url": row.get("href", "").split("?")[0],
                "original_price": original_el.text.strip(),
            })

        return candidates

    def _build_game(self, candidate: dict) -> FreeGame:
        """Enrich a candidate with app details and review score, then return a FreeGame."""
        appid = candidate["appid"]
        details = self._fetch_appdetails(appid)
        review_score = self._fetch_review_score(appid)

        image_url = details.get("header_image") or (
            f"https://shared.akamai.steamstatic.com/store_item_assets"
            f"/steam/apps/{appid}/capsule_sm_120.jpg"
        )
        end_date = self._fetch_end_date(candidate["url"])

        logger.info("Built free game: %s (appid=%s, review=%s)", candidate["title"], appid, review_score)
        return FreeGame(
            title=candidate["title"],
            store=self.store_name,
            url=candidate["url"],
            image_url=image_url,
            original_price=candidate["original_price"],
            end_date=end_date,
            is_permanent=False,
            description=details.get("short_description", ""),
            review_score=review_score,
        )

    def _fetch_appdetails(self, appid: str) -> dict:
        """Fetch short_description and header_image from the Steam appdetails API."""
        try:
            response = requests.get(
                _APPDETAILS_URL,
                params={"appids": appid, "cc": "US", "l": "english"},
                headers=_HEADERS,
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get(appid, {}).get("success"):
                    return data[appid]["data"]
        except Exception as e:
            logger.warning("Failed to fetch appdetails for appid=%s: %s", appid, e)
        return {}

    def _fetch_end_date(self, url: str) -> str:
        """Scrape the discount expiration from the game's store page.

        Steam shows 'Free to keep when you get it before DD Mon @ HH:MMam/pm'
        on the store page. The time is in UTC when scraped without session cookies.
        """
        try:
            response = requests.get(url, headers=_HEADERS, timeout=10)
            if response.status_code != 200:
                return ""
            soup = BeautifulSoup(response.text, "html.parser")
            el = soup.select_one(".game_purchase_discount_quantity")
            if not el:
                return ""
            return _parse_steam_end_date(el.text)
        except Exception as e:
            logger.warning("Failed to fetch end date from %s: %s", url, e)
            return ""

    def _fetch_review_score(self, appid: str) -> Optional[str]:
        """Fetch user review summary label from the Steam reviews API."""
        try:
            response = requests.get(
                f"{_APPREVIEWS_URL}/{appid}",
                params={"json": 1, "language": "all", "purchase_type": "all"},
                headers=_HEADERS,
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("query_summary", {}).get("review_score_desc") or None
        except Exception as e:
            logger.warning("Failed to fetch review score for appid=%s: %s", appid, e)
        return None
