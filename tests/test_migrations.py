"""Tests for the database migration runner in main.py."""

import importlib
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


class TestMainDbBranch:
    """Tests for the DB-enabled branch of main()."""

    def test_runs_migrations_when_db_host_is_set(self):
        """main() should call _run_db_migrations when DB_HOST is configured."""
        main = _import_main()

        mock_db = MagicMock()
        with patch("main.DB_HOST", "localhost"), \
             patch("main.FreeGamesDatabase", return_value=mock_db), \
             patch("main._run_db_migrations") as mock_migrate, \
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

    def test_does_not_run_migrations_when_db_host_is_not_set(self):
        """main() should skip DB init and migrations when DB_HOST is not set."""
        main = _import_main()

        with patch("main.DB_HOST", None), \
             patch("main._run_db_migrations") as mock_migrate, \
             patch("main.FreeGamesDatabase") as mock_db_cls, \
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
