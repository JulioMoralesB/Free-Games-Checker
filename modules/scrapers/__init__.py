"""Game store scrapers package."""

from modules.scrapers.base import BaseScraper
from modules.scrapers.epic import EpicGamesScraper
from modules.scrapers.steam import SteamScraper

__all__ = ["BaseScraper", "EpicGamesScraper", "SteamScraper"]
