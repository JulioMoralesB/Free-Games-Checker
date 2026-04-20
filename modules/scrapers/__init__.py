"""Game store scrapers package."""

import logging
from typing import Iterable

from modules.scrapers.base import BaseScraper
from modules.scrapers.epic import EpicGamesScraper
from modules.scrapers.steam import SteamScraper

logger = logging.getLogger(__name__)

SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "epic": EpicGamesScraper,
    "steam": SteamScraper,
}


def get_enabled_scrapers(enabled_stores: Iterable[str]) -> list[BaseScraper]:
    """Instantiate scrapers for the given store identifiers.

    Unknown store names are skipped with a warning so a misconfigured
    ENABLED_STORES entry does not prevent the remaining scrapers from running.
    If none of the requested stores are recognized, the Epic scraper is
    returned as a safe default.
    """
    scrapers: list[BaseScraper] = []
    for name in enabled_stores:
        scraper_cls = SCRAPER_REGISTRY.get(name)
        if scraper_cls is None:
            logger.warning(
                "Unknown store '%s' in ENABLED_STORES; known stores: %s",
                name,
                sorted(SCRAPER_REGISTRY.keys()),
            )
            continue
        scrapers.append(scraper_cls())

    if not scrapers:
        logger.warning(
            "No valid stores resolved from ENABLED_STORES=%s; defaulting to 'epic'.",
            list(enabled_stores),
        )
        scrapers.append(EpicGamesScraper())

    return scrapers


__all__ = [
    "BaseScraper",
    "EpicGamesScraper",
    "SteamScraper",
    "SCRAPER_REGISTRY",
    "get_enabled_scrapers",
]
