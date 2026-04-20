from modules.scrapers import (
    SCRAPER_REGISTRY,
    EpicGamesScraper,
    SteamScraper,
    get_enabled_scrapers,
)


class TestScraperRegistry:
    def test_registry_contains_epic_and_steam(self):
        assert SCRAPER_REGISTRY["epic"] is EpicGamesScraper
        assert SCRAPER_REGISTRY["steam"] is SteamScraper

    def test_returns_only_epic_by_default(self):
        scrapers = get_enabled_scrapers(["epic"])

        assert len(scrapers) == 1
        assert isinstance(scrapers[0], EpicGamesScraper)

    def test_returns_both_when_both_enabled(self):
        scrapers = get_enabled_scrapers(["epic", "steam"])

        assert [s.store_name for s in scrapers] == ["epic", "steam"]
        assert isinstance(scrapers[0], EpicGamesScraper)
        assert isinstance(scrapers[1], SteamScraper)

    def test_returns_only_steam_when_steam_enabled(self):
        scrapers = get_enabled_scrapers(["steam"])

        assert len(scrapers) == 1
        assert isinstance(scrapers[0], SteamScraper)

    def test_skips_unknown_stores_but_keeps_valid_ones(self, caplog):
        with caplog.at_level("WARNING"):
            scrapers = get_enabled_scrapers(["epic", "bogus"])

        assert [s.store_name for s in scrapers] == ["epic"]
        assert "bogus" in caplog.text

    def test_falls_back_to_epic_when_all_unknown(self, caplog):
        with caplog.at_level("WARNING"):
            scrapers = get_enabled_scrapers(["nope"])

        assert len(scrapers) == 1
        assert isinstance(scrapers[0], EpicGamesScraper)

    def test_falls_back_to_epic_when_empty(self, caplog):
        with caplog.at_level("WARNING"):
            scrapers = get_enabled_scrapers([])

        assert len(scrapers) == 1
        assert isinstance(scrapers[0], EpicGamesScraper)
