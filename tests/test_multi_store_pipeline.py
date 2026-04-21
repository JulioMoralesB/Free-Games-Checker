"""Integration tests for the multi-store check_games pipeline.

Verifies that check_games correctly runs multiple scrapers, aggregates their
results into a single notification batch, and applies deduplication against
previously seen games regardless of which store they came from.
"""

import sys
import pytest
from unittest.mock import patch, MagicMock

from modules.models import FreeGame


def _import_main():
    sys.modules.pop("main", None)
    with patch("logging.handlers.TimedRotatingFileHandler"):
        import main as _main
    return _main


def _epic_game(title, url, end_date="2099-01-01T00:00:00.000Z"):
    return FreeGame(
        title=title,
        store="epic",
        url=url,
        image_url="https://example.com/epic.png",
        original_price=None,
        end_date=end_date,
        is_permanent=False,
        description="Epic game",
    )


def _steam_game(title, url, end_date="2099-01-01T00:00:00.000Z"):
    return FreeGame(
        title=title,
        store="steam",
        url=url,
        image_url="https://example.com/steam.png",
        original_price="$9.99",
        end_date=end_date,
        is_permanent=False,
        description="Steam game",
    )


class TestMultiStorePipeline:
    """check_games with both Epic and Steam scrapers enabled."""

    def test_fetches_from_both_scrapers_and_notifies_combined(self):
        """A single Discord notification should contain new games from both stores."""
        main = _import_main()

        epic_game = _epic_game("Epic Freebie", "https://store.epicgames.com/p/epic-freebie")
        steam_game = _steam_game("Steam Freebie", "https://store.steampowered.com/app/1/steam-freebie")

        with patch("main.ENABLED_STORES", ["epic", "steam"]), \
             patch("modules.scrapers.epic.EpicGamesScraper.fetch_free_games", return_value=[epic_game]), \
             patch("modules.scrapers.steam.SteamScraper.fetch_free_games", return_value=[steam_game]), \
             patch("main.load_previous_games", return_value=[]), \
             patch("main.send_discord_message") as mock_send, \
             patch("main.save_last_notification"), \
             patch("main.save_games"):
            main.check_games()

        mock_send.assert_called_once()
        notified = mock_send.call_args[0][0]
        assert len(notified) == 2
        stores = {g.store for g in notified}
        assert stores == {"epic", "steam"}

    def test_only_new_games_are_notified_across_stores(self):
        """Games already in previous_games (from any store) must not trigger a notification."""
        main = _import_main()

        known_epic = _epic_game("Known Epic Game", "https://store.epicgames.com/p/known-epic")
        new_steam = _steam_game("New Steam Game", "https://store.steampowered.com/app/2/new-steam")

        with patch("main.ENABLED_STORES", ["epic", "steam"]), \
             patch("modules.scrapers.epic.EpicGamesScraper.fetch_free_games", return_value=[known_epic]), \
             patch("modules.scrapers.steam.SteamScraper.fetch_free_games", return_value=[new_steam]), \
             patch("main.load_previous_games", return_value=[known_epic]), \
             patch("main.send_discord_message") as mock_send, \
             patch("main.save_last_notification"), \
             patch("main.save_games"):
            main.check_games()

        mock_send.assert_called_once()
        notified = mock_send.call_args[0][0]
        assert len(notified) == 1
        assert notified[0].store == "steam"
        assert notified[0].title == "New Steam Game"

    def test_no_notification_when_all_games_already_seen(self):
        """No Discord call when every game from both stores is already in previous_games."""
        main = _import_main()

        epic_game = _epic_game("Old Epic", "https://store.epicgames.com/p/old-epic")
        steam_game = _steam_game("Old Steam", "https://store.steampowered.com/app/3/old-steam")

        with patch("main.ENABLED_STORES", ["epic", "steam"]), \
             patch("modules.scrapers.epic.EpicGamesScraper.fetch_free_games", return_value=[epic_game]), \
             patch("modules.scrapers.steam.SteamScraper.fetch_free_games", return_value=[steam_game]), \
             patch("main.load_previous_games", return_value=[epic_game, steam_game]), \
             patch("main.send_discord_message") as mock_send, \
             patch("main.save_last_notification") as mock_save_notif, \
             patch("main.save_games") as mock_save:
            main.check_games()

        mock_send.assert_not_called()
        mock_save_notif.assert_not_called()
        mock_save.assert_called_once_with([epic_game, steam_game])

    def test_steam_failure_does_not_prevent_epic_notification(self):
        """If the Steam scraper raises, Epic games are still fetched and notified."""
        main = _import_main()

        epic_game = _epic_game("Epic Only", "https://store.epicgames.com/p/epic-only")

        with patch("main.ENABLED_STORES", ["epic", "steam"]), \
             patch("modules.scrapers.epic.EpicGamesScraper.fetch_free_games", return_value=[epic_game]), \
             patch("modules.scrapers.steam.SteamScraper.fetch_free_games", side_effect=RuntimeError("Steam down")), \
             patch("main.load_previous_games", return_value=[]), \
             patch("main.send_discord_message") as mock_send, \
             patch("main.save_last_notification"), \
             patch("main.save_games"):
            main.check_games()

        mock_send.assert_called_once()
        notified = mock_send.call_args[0][0]
        assert len(notified) == 1
        assert notified[0].store == "epic"

    def test_epic_failure_does_not_prevent_steam_notification(self):
        """If the Epic scraper raises, Steam games are still fetched and notified."""
        main = _import_main()

        steam_game = _steam_game("Steam Only", "https://store.steampowered.com/app/4/steam-only")

        with patch("main.ENABLED_STORES", ["epic", "steam"]), \
             patch("modules.scrapers.epic.EpicGamesScraper.fetch_free_games", side_effect=RuntimeError("Epic down")), \
             patch("modules.scrapers.steam.SteamScraper.fetch_free_games", return_value=[steam_game]), \
             patch("main.load_previous_games", return_value=[]), \
             patch("main.send_discord_message") as mock_send, \
             patch("main.save_last_notification"), \
             patch("main.save_games"):
            main.check_games()

        mock_send.assert_called_once()
        notified = mock_send.call_args[0][0]
        assert len(notified) == 1
        assert notified[0].store == "steam"

    def test_save_games_receives_all_store_results_combined(self):
        """save_games should be called with the full combined list from all scrapers."""
        main = _import_main()

        epic_game = _epic_game("Epic Save", "https://store.epicgames.com/p/epic-save")
        steam_game = _steam_game("Steam Save", "https://store.steampowered.com/app/5/steam-save")

        with patch("main.ENABLED_STORES", ["epic", "steam"]), \
             patch("modules.scrapers.epic.EpicGamesScraper.fetch_free_games", return_value=[epic_game]), \
             patch("modules.scrapers.steam.SteamScraper.fetch_free_games", return_value=[steam_game]), \
             patch("main.load_previous_games", return_value=[epic_game, steam_game]), \
             patch("main.send_discord_message"), \
             patch("main.save_last_notification"), \
             patch("main.save_games") as mock_save:
            main.check_games()

        mock_save.assert_called_once()
        saved = mock_save.call_args[0][0]
        assert len(saved) == 2
        assert {g.store for g in saved} == {"epic", "steam"}
