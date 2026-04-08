import json
import os
import pytest
from unittest.mock import patch, MagicMock

from modules import storage
from modules.models import FreeGame


# ---------------------------------------------------------------------------
# Tests for load_previous_games
# ---------------------------------------------------------------------------

class TestLoadPreviousGames:
    def test_returns_empty_list_when_file_not_exists(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result == []

    def test_loads_valid_json_file(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with open(path, "w") as f:
            json.dump([g.to_dict() for g in sample_games], f)
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result == sample_games

    def test_returns_empty_list_on_corrupted_json(self, tmp_path):
        path = str(tmp_path / "games.json")
        with open(path, "w") as f:
            f.write("this is not valid json {{{{")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result == []

    def test_returns_empty_list_when_data_is_not_a_list(self, tmp_path):
        path = str(tmp_path / "games.json")
        with open(path, "w") as f:
            json.dump({"key": "value"}, f)
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result == []

    def test_returns_empty_list_when_items_are_not_dicts(self, tmp_path):
        path = str(tmp_path / "games.json")
        with open(path, "w") as f:
            json.dump(["game1", "game2"], f)
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result == []

    def test_returns_empty_list_on_io_error(self, tmp_path):
        path = str(tmp_path / "games.json")
        (tmp_path / "games.json").write_text("[]")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path), \
             patch("builtins.open", side_effect=IOError("disk read error")):
            result = storage.load_previous_games()
        assert result == []

    def test_loaded_games_preserve_all_fields(self, tmp_path, sample_game):
        path = str(tmp_path / "games.json")
        with open(path, "w") as f:
            json.dump([sample_game.to_dict()], f)
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result[0].title == sample_game.title
        assert result[0].url == sample_game.url
        assert result[0].end_date == sample_game.end_date
        assert result[0].description == sample_game.description
        assert result[0].image_url == sample_game.image_url


# ---------------------------------------------------------------------------
# Tests for save_games
# ---------------------------------------------------------------------------

class TestSaveGames:
    def test_saves_games_to_file(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            storage.save_games(sample_games)
        with open(path, "r") as f:
            saved = json.load(f)
        assert saved == [g.to_dict() for g in sample_games]

    def test_does_not_write_when_games_is_empty(self, tmp_path):
        path = str(tmp_path / "games.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            storage.save_games([])
        assert not os.path.exists(path)

    def test_creates_directory_if_missing(self, tmp_path, sample_games):
        sub_dir = tmp_path / "nested" / "dir"
        path = str(sub_dir / "games.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            storage.save_games(sample_games)
        assert os.path.exists(path)

    def test_raises_io_error_on_permission_error(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path), \
             patch("builtins.open", side_effect=PermissionError("denied")):
            with pytest.raises(IOError):
                storage.save_games(sample_games)

    def test_raises_type_error_on_unserializable_data(self, tmp_path):
        from unittest.mock import patch as _patch
        from modules.models import FreeGame
        path = str(tmp_path / "games.json")
        game = FreeGame(
            title="Test", store="epic", url="https://example.com", image_url="",
            original_price=None, end_date="", is_permanent=False, description="",
        )
        # Simulate to_dict returning an object() which is not JSON-serialisable
        unserializable = {"title": object()}
        with _patch.object(game, "to_dict", return_value=unserializable):
            games = [game]
            with patch("modules.storage.DB_HOST", None), \
                 patch("modules.storage.DATA_FILE_PATH", path):
                with pytest.raises(TypeError):
                    storage.save_games(games)

    def test_saved_file_is_valid_json(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            storage.save_games(sample_games)
        with open(path, "r") as f:
            content = f.read()
        parsed = json.loads(content)
        assert isinstance(parsed, list)

    def test_save_then_load_round_trip(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            storage.save_games(sample_games)
            loaded = storage.load_previous_games()
        assert loaded == sample_games


# ---------------------------------------------------------------------------
# Tests for PostgreSQL-backed storage
# ---------------------------------------------------------------------------

class TestDatabaseBackedLoadPreviousGames:
    def test_delegates_to_db_when_db_host_is_set(self, sample_games):
        mock_db = MagicMock()
        mock_db.get_games.return_value = sample_games
        with patch("modules.storage.DB_HOST", "localhost"), \
             patch("modules.database.FreeGamesDatabase", return_value=mock_db):
            result = storage.load_previous_games()
        assert result == sample_games
        mock_db.get_games.assert_called_once()

    def test_returns_empty_list_when_db_raises(self):
        mock_db = MagicMock()
        mock_db.get_games.side_effect = Exception("connection refused")
        with patch("modules.storage.DB_HOST", "localhost"), \
             patch("modules.database.FreeGamesDatabase", return_value=mock_db):
            result = storage.load_previous_games()
        assert result == []

    def test_uses_file_backend_when_db_host_not_set(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with open(path, "w") as f:
            json.dump([g.to_dict() for g in sample_games], f)
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result == sample_games


class TestDatabaseBackedSaveGames:
    def test_delegates_to_db_when_db_host_is_set(self, sample_games):
        mock_db = MagicMock()
        with patch("modules.storage.DB_HOST", "localhost"), \
             patch("modules.database.FreeGamesDatabase", return_value=mock_db):
            storage.save_games(sample_games)
        mock_db.save_games.assert_called_once_with(sample_games)

    def test_raises_io_error_when_db_save_fails(self, sample_games):
        mock_db = MagicMock()
        mock_db.save_games.side_effect = Exception("db write error")
        with patch("modules.storage.DB_HOST", "localhost"), \
             patch("modules.database.FreeGamesDatabase", return_value=mock_db):
            with pytest.raises(IOError):
                storage.save_games(sample_games)

    def test_does_not_call_db_save_for_empty_list(self):
        mock_db = MagicMock()
        with patch("modules.storage.DB_HOST", "localhost"), \
             patch("modules.database.FreeGamesDatabase", return_value=mock_db):
            storage.save_games([])
        mock_db.save_games.assert_not_called()

    def test_uses_file_backend_when_db_host_not_set(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.DATA_FILE_PATH", path):
            storage.save_games(sample_games)
        with open(path, "r") as f:
            saved = json.load(f)
        assert saved == [g.to_dict() for g in sample_games]


# ---------------------------------------------------------------------------
# Tests for save_last_notification and load_last_notification
# ---------------------------------------------------------------------------

class TestSaveLastNotification:
    def test_saves_games_to_file_when_db_not_configured(self, tmp_path, sample_games):
        path = str(tmp_path / "last_notification.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.LAST_NOTIFICATION_FILE_PATH", path):
            storage.save_last_notification(sample_games)
        with open(path, "r") as f:
            saved = json.load(f)
        assert saved == [g.to_dict() for g in sample_games]

    def test_does_not_write_when_games_is_empty(self, tmp_path):
        path = str(tmp_path / "last_notification.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.LAST_NOTIFICATION_FILE_PATH", path):
            storage.save_last_notification([])
        assert not os.path.exists(path)

    def test_creates_directory_if_missing(self, tmp_path, sample_games):
        sub_dir = tmp_path / "nested" / "dir"
        path = str(sub_dir / "last_notification.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.LAST_NOTIFICATION_FILE_PATH", path):
            storage.save_last_notification(sample_games)
        assert os.path.exists(path)

    def test_raises_io_error_on_file_failure(self, tmp_path, sample_games):
        path = str(tmp_path / "last_notification.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.LAST_NOTIFICATION_FILE_PATH", path), \
             patch("builtins.open", side_effect=PermissionError("denied")):
            with pytest.raises(IOError):
                storage.save_last_notification(sample_games)

    def test_saved_file_is_valid_json(self, tmp_path, sample_games):
        path = str(tmp_path / "last_notification.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.LAST_NOTIFICATION_FILE_PATH", path):
            storage.save_last_notification(sample_games)
        with open(path, "r") as f:
            parsed = json.loads(f.read())
        assert isinstance(parsed, list)

    def test_delegates_to_db_when_db_configured(self, sample_games):
        mock_db = MagicMock()
        with patch("modules.storage.DB_HOST", "localhost"), \
             patch("modules.database.FreeGamesDatabase", return_value=mock_db):
            storage.save_last_notification(sample_games)
        mock_db.save_last_notification.assert_called_once_with(sample_games)

    def test_raises_io_error_when_db_save_fails(self, sample_games):
        mock_db = MagicMock()
        mock_db.save_last_notification.side_effect = Exception("db write error")
        with patch("modules.storage.DB_HOST", "localhost"), \
             patch("modules.database.FreeGamesDatabase", return_value=mock_db):
            with pytest.raises(IOError):
                storage.save_last_notification(sample_games)


class TestLoadLastNotification:
    def test_returns_empty_list_when_file_not_exists(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.LAST_NOTIFICATION_FILE_PATH", path):
            result = storage.load_last_notification()
        assert result == []

    def test_loads_valid_json_file(self, tmp_path, sample_games):
        path = str(tmp_path / "last_notification.json")
        with open(path, "w") as f:
            json.dump([g.to_dict() for g in sample_games], f)
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.LAST_NOTIFICATION_FILE_PATH", path):
            result = storage.load_last_notification()
        assert result == sample_games

    def test_returns_empty_list_on_corrupted_json(self, tmp_path):
        path = str(tmp_path / "last_notification.json")
        with open(path, "w") as f:
            f.write("not valid json {{")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.LAST_NOTIFICATION_FILE_PATH", path):
            result = storage.load_last_notification()
        assert result == []

    def test_returns_empty_list_when_data_is_not_a_list(self, tmp_path):
        path = str(tmp_path / "last_notification.json")
        with open(path, "w") as f:
            json.dump({"key": "value"}, f)
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.LAST_NOTIFICATION_FILE_PATH", path):
            result = storage.load_last_notification()
        assert result == []

    def test_returns_empty_list_when_items_are_not_dicts(self, tmp_path):
        path = str(tmp_path / "last_notification.json")
        with open(path, "w") as f:
            json.dump(["game1", "game2"], f)
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.LAST_NOTIFICATION_FILE_PATH", path):
            result = storage.load_last_notification()
        assert result == []

    def test_save_then_load_round_trip(self, tmp_path, sample_games):
        path = str(tmp_path / "last_notification.json")
        with patch("modules.storage.DB_HOST", None), \
             patch("modules.storage.LAST_NOTIFICATION_FILE_PATH", path):
            storage.save_last_notification(sample_games)
            result = storage.load_last_notification()
        assert result == sample_games

    def test_delegates_to_db_when_db_configured(self, sample_games):
        mock_db = MagicMock()
        mock_db.get_last_notification.return_value = sample_games
        with patch("modules.storage.DB_HOST", "localhost"), \
             patch("modules.database.FreeGamesDatabase", return_value=mock_db):
            result = storage.load_last_notification()
        assert result == sample_games
        mock_db.get_last_notification.assert_called_once()

    def test_returns_empty_list_when_db_raises(self):
        mock_db = MagicMock()
        mock_db.get_last_notification.side_effect = Exception("connection refused")
        with patch("modules.storage.DB_HOST", "localhost"), \
             patch("modules.database.FreeGamesDatabase", return_value=mock_db):
            result = storage.load_last_notification()
        assert result == []


# ---------------------------------------------------------------------------
# Tests for FreeGamesDatabase.get_last_notification validation
# ---------------------------------------------------------------------------

class TestFreeGamesDatabaseGetLastNotification:
    """Unit-test the validation logic inside FreeGamesDatabase.get_last_notification()."""

    def _make_db(self):
        from modules.database import FreeGamesDatabase
        db = FreeGamesDatabase.__new__(FreeGamesDatabase)
        db.conn_params = {}
        return db

    def _mock_conn(self, row):
        """Return a context-manager chain for psycopg2.connect that yields *row*."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = row
        mock_cursor.__enter__ = lambda s: s
        mock_cursor.__exit__ = MagicMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)

        return mock_conn

    def test_returns_empty_list_when_no_row(self):
        db = self._make_db()
        mock_conn = self._mock_conn(None)
        with patch("modules.database.psycopg2.connect", return_value=mock_conn):
            result = db.get_last_notification()
        assert result == []

    def test_returns_games_for_valid_list(self, sample_games):
        db = self._make_db()
        mock_conn = self._mock_conn((json.dumps([g.to_dict() for g in sample_games]),))
        with patch("modules.database.psycopg2.connect", return_value=mock_conn):
            result = db.get_last_notification()
        assert result == sample_games

    def test_returns_empty_list_when_data_is_not_a_list(self):
        db = self._make_db()
        mock_conn = self._mock_conn((json.dumps({"key": "value"}),))
        with patch("modules.database.psycopg2.connect", return_value=mock_conn):
            result = db.get_last_notification()
        assert result == []

    def test_returns_empty_list_when_items_are_not_dicts(self):
        db = self._make_db()
        mock_conn = self._mock_conn((json.dumps(["game1", "game2"]),))
        with patch("modules.database.psycopg2.connect", return_value=mock_conn):
            result = db.get_last_notification()
        assert result == []
