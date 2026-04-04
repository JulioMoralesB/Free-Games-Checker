"""Tests for the database migration runner in main.py."""

import sys
import pytest
from unittest.mock import patch, MagicMock


def _import_main():
    """Import (or reimport) main with the log-file handler mocked out.

    main.py creates a TimedRotatingFileHandler at module level which requires
    /mnt/logs/notifier.log to exist.  In the test environment this path is not
    available, so we mock the handler class before the module is loaded.
    """
    # Remove cached module so it is re-executed under the mock.
    sys.modules.pop("main", None)
    with patch("logging.handlers.TimedRotatingFileHandler"):
        import main as _main
    return _main


class TestRunDbMigrations:
    """Tests for main._run_db_migrations()."""

    def test_calls_alembic_upgrade_head(self):
        """_run_db_migrations should invoke alembic upgrade with 'head'."""
        main = _import_main()

        mock_upgrade = MagicMock()
        with patch("main.alembic_command.upgrade", mock_upgrade):
            main._run_db_migrations()

        assert mock_upgrade.call_count == 1
        _, upgrade_target = mock_upgrade.call_args[0]
        assert upgrade_target == "head"

    def test_passes_alembic_config_object(self):
        """_run_db_migrations should pass an AlembicConfig instance to upgrade."""
        from alembic.config import Config as AlembicConfig
        main = _import_main()

        captured_cfg = {}

        def capture_upgrade(cfg, target):
            captured_cfg["cfg"] = cfg

        with patch("main.alembic_command.upgrade", side_effect=capture_upgrade):
            main._run_db_migrations()

        assert isinstance(captured_cfg["cfg"], AlembicConfig)

    def test_propagates_alembic_exception(self):
        """_run_db_migrations should not swallow exceptions from alembic."""
        main = _import_main()

        with patch("main.alembic_command.upgrade", side_effect=RuntimeError("db error")):
            with pytest.raises(RuntimeError, match="db error"):
                main._run_db_migrations()


class TestVerifyRequiredTables:
    """Tests for main._verify_required_tables()."""

    def test_succeeds_when_last_notification_exists(self):
        """Verification should pass when the required table exists."""
        main = _import_main()

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("free_games.last_notification",)

        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("main.psycopg2.connect", return_value=mock_conn):
            main._verify_required_tables()

    def test_raises_when_last_notification_is_missing(self):
        """Verification should fail fast when last_notification table is absent."""
        main = _import_main()

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None,)

        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("main.psycopg2.connect", return_value=mock_conn):
            with pytest.raises(RuntimeError, match="last_notification"):
                main._verify_required_tables()


class TestMainDbBranch:
    """Tests for the DB-enabled branch of main()."""

    def test_runs_migrations_when_db_host_is_set(self):
        """main() should call _run_db_migrations when DB_HOST is configured."""
        main = _import_main()

        mock_db = MagicMock()
        with patch("main.DB_HOST", "localhost"), \
             patch("main.FreeGamesDatabase", return_value=mock_db), \
             patch("main._run_db_migrations") as mock_migrate, \
             patch("main._verify_required_tables") as mock_verify_tables, \
             patch("main._start_api_server"), \
             patch("main.check_games"), \
             patch("main.healthcheck"), \
             patch("main.schedule"), \
             patch("main.time.sleep", side_effect=KeyboardInterrupt):
            try:
                main.main()
            except KeyboardInterrupt:
                pass

        mock_db.init_db.assert_called_once()
        mock_migrate.assert_called_once()
        mock_verify_tables.assert_called_once()

    def test_does_not_run_migrations_when_db_host_is_not_set(self):
        """main() should skip DB init and migrations when DB_HOST is not set."""
        main = _import_main()

        with patch("main.DB_HOST", None), \
             patch("main._run_db_migrations") as mock_migrate, \
             patch("main._verify_required_tables") as mock_verify_tables, \
             patch("main.FreeGamesDatabase") as mock_db_cls, \
             patch("main._start_api_server"), \
             patch("main.check_games"), \
             patch("main.healthcheck"), \
             patch("main.schedule"), \
             patch("main.time.sleep", side_effect=KeyboardInterrupt):
            try:
                main.main()
            except KeyboardInterrupt:
                pass

        mock_db_cls.assert_not_called()
        mock_migrate.assert_not_called()
        mock_verify_tables.assert_not_called()


class TestCheckGamesDedupe:
    """Tests for check_games new-game detection behavior."""

    def test_does_not_notify_when_only_non_identity_fields_change(self):
        """No Discord notification should be sent when only thumbnail/description changes."""
        main = _import_main()

        previous_games = [
            {
                "title": "TOMAK: Save the Earth Regeneration",
                "link": "https://store.epicgames.com/es-MX/p/tomak-save-the-earth-regeneration-c1207c",
                "description": "old description",
                "thumbnail": "https://cdn1.epicgames.com/old-image.png",
                "end_date": "2026-04-16T15:00:00.000Z",
            }
        ]
        current_games = [
            {
                "title": "TOMAK: Save the Earth Regeneration",
                "link": "https://store.epicgames.com/es-MX/p/tomak-save-the-earth-regeneration-c1207c",
                "description": "new description",
                "thumbnail": "https://cdn1.epicgames.com/new-image.png",
                "end_date": "2026-04-16T15:00:00.000Z",
            }
        ]

        with patch("main.fetch_free_games", return_value=current_games), \
             patch("main.load_previous_games", return_value=previous_games), \
             patch("main.send_discord_message") as mock_send_discord, \
             patch("main.save_last_notification") as mock_save_last_notification, \
             patch("main.save_games") as mock_save_games:
            main.check_games()

        mock_send_discord.assert_not_called()
        mock_save_last_notification.assert_not_called()
        mock_save_games.assert_called_once_with(current_games)

    def test_notifies_when_link_is_new(self):
        """Discord notification should be sent only for games with unseen links."""
        main = _import_main()

        previous_games = [
            {
                "title": "Old Game",
                "link": "https://store.epicgames.com/es-MX/p/old-game",
                "description": "desc",
                "thumbnail": "https://example.com/old.png",
                "end_date": "2026-04-09T15:00:00.000Z",
            }
        ]
        current_games = [
            {
                "title": "Old Game",
                "link": "https://store.epicgames.com/es-MX/p/old-game",
                "description": "updated desc",
                "thumbnail": "https://example.com/old-new.png",
                "end_date": "2026-04-09T15:00:00.000Z",
            },
            {
                "title": "Brand New Game",
                "link": "https://store.epicgames.com/es-MX/p/brand-new-game",
                "description": "desc",
                "thumbnail": "https://example.com/new.png",
                "end_date": "2026-04-16T15:00:00.000Z",
            },
        ]

        with patch("main.fetch_free_games", return_value=current_games), \
             patch("main.load_previous_games", return_value=previous_games), \
             patch("main.send_discord_message") as mock_send_discord, \
             patch("main.save_last_notification") as mock_save_last_notification, \
             patch("main.save_games") as mock_save_games:
            main.check_games()

        mock_send_discord.assert_called_once_with([current_games[1]])
        mock_save_last_notification.assert_called_once_with([current_games[1]])
        mock_save_games.assert_called_once_with(current_games)

    def test_notifies_again_when_previous_promo_has_expired(self):
        """A game can be notified again when its prior free period has already ended."""
        main = _import_main()

        previous_games = [
            {
                "title": "Recurring Game",
                "link": "https://store.epicgames.com/es-MX/p/recurring-game",
                "description": "old",
                "thumbnail": "https://example.com/old.png",
                "end_date": "2025-10-01T15:00:00.000Z",
            }
        ]
        current_games = [
            {
                "title": "Recurring Game",
                "link": "https://store.epicgames.com/es-MX/p/recurring-game",
                "description": "new",
                "thumbnail": "https://example.com/new.png",
                "end_date": "2026-10-01T15:00:00.000Z",
            }
        ]

        with patch("main.fetch_free_games", return_value=current_games), \
             patch("main.load_previous_games", return_value=previous_games), \
             patch("main.send_discord_message") as mock_send_discord, \
             patch("main.save_last_notification") as mock_save_last_notification, \
             patch("main.save_games") as mock_save_games:
            main.check_games()

        mock_send_discord.assert_called_once_with(current_games)
        mock_save_last_notification.assert_called_once_with(current_games)
        mock_save_games.assert_called_once_with(current_games)

    def test_does_not_notify_when_previous_promo_is_still_active(self):
        """No duplicate notification while the previously notified promo is still active."""
        main = _import_main()

        previous_games = [
            {
                "title": "Still Free",
                "link": "https://store.epicgames.com/es-MX/p/still-free",
                "description": "old",
                "thumbnail": "https://example.com/old.png",
                "end_date": "2099-10-01T15:00:00.000Z",
            }
        ]
        current_games = [
            {
                "title": "Still Free",
                "link": "https://store.epicgames.com/es-MX/p/still-free",
                "description": "new",
                "thumbnail": "https://example.com/new.png",
                "end_date": "2099-10-01T15:00:00.000Z",
            }
        ]

        with patch("main.fetch_free_games", return_value=current_games), \
             patch("main.load_previous_games", return_value=previous_games), \
             patch("main.send_discord_message") as mock_send_discord, \
             patch("main.save_last_notification") as mock_save_last_notification, \
             patch("main.save_games") as mock_save_games:
            main.check_games()

        mock_send_discord.assert_not_called()
        mock_save_last_notification.assert_not_called()
        mock_save_games.assert_called_once_with(current_games)


class TestFindNewGamesEdgeCases:
    """Tests for _find_new_games / _is_still_active edge cases."""

    def test_missing_end_date_treated_as_active(self):
        """A previous game with no end_date should be treated as still active (no re-notify)."""
        main = _import_main()

        previous_games = [
            {
                "title": "Free Game",
                "link": "https://store.epicgames.com/es-MX/p/free-game",
                "description": "desc",
                "thumbnail": "https://example.com/img.png",
                # end_date intentionally absent
            }
        ]
        current_games = [
            {
                "title": "Free Game",
                "link": "https://store.epicgames.com/es-MX/p/free-game",
                "description": "updated desc",
                "thumbnail": "https://example.com/img.png",
            }
        ]

        result = main._find_new_games(current_games, previous_games)

        assert result == [], "Missing end_date should be treated as active; no new games expected"

    def test_none_end_date_treated_as_active(self):
        """A previous game with end_date=None should be treated as still active."""
        main = _import_main()

        previous_games = [
            {
                "title": "Free Game",
                "link": "https://store.epicgames.com/es-MX/p/free-game",
                "end_date": None,
            }
        ]
        current_games = [
            {
                "title": "Free Game",
                "link": "https://store.epicgames.com/es-MX/p/free-game",
                "end_date": None,
            }
        ]

        result = main._find_new_games(current_games, previous_games)

        assert result == [], "end_date=None should be treated as active; no new games expected"

    def test_malformed_end_date_treated_as_active(self):
        """A previous game with a malformed end_date (non-ISO string) should be treated as still active."""
        main = _import_main()

        previous_games = [
            {
                "title": "Free Game",
                "link": "https://store.epicgames.com/es-MX/p/free-game",
                "end_date": "not-a-valid-date",
            }
        ]
        current_games = [
            {
                "title": "Free Game",
                "link": "https://store.epicgames.com/es-MX/p/free-game",
                "end_date": "2099-01-01T00:00:00.000Z",
            }
        ]

        result = main._find_new_games(current_games, previous_games)

        assert result == [], "Malformed end_date should be treated as active; no new games expected"

    def test_naive_datetime_without_tzinfo_treated_as_future(self):
        """A previous game with a naive ISO datetime (no timezone) should be assigned UTC and handled correctly."""
        main = _import_main()

        # A naive far-future date that should be treated as active.
        previous_games = [
            {
                "title": "Free Game",
                "link": "https://store.epicgames.com/es-MX/p/free-game",
                "end_date": "2099-01-01T00:00:00",  # no timezone suffix
            }
        ]
        current_games = [
            {
                "title": "Free Game",
                "link": "https://store.epicgames.com/es-MX/p/free-game",
                "end_date": "2099-01-01T00:00:00",
            }
        ]

        result = main._find_new_games(current_games, previous_games)

        assert result == [], "Naive far-future end_date should be treated as active after UTC assignment"

    def test_naive_datetime_in_past_treated_as_expired(self):
        """A previous game with a naive ISO datetime in the past should be treated as expired."""
        main = _import_main()

        previous_games = [
            {
                "title": "Free Game",
                "link": "https://store.epicgames.com/es-MX/p/free-game",
                "end_date": "2000-01-01T00:00:00",  # naive past date
            }
        ]
        current_games = [
            {
                "title": "Free Game",
                "link": "https://store.epicgames.com/es-MX/p/free-game",
                "end_date": "2099-01-01T00:00:00",
            }
        ]

        result = main._find_new_games(current_games, previous_games)

        assert result == current_games, "Naive past end_date should be treated as expired; game should appear as new"
