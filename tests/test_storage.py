import json
import os
import pytest
from unittest.mock import patch, MagicMock

from modules import storage


# ---------------------------------------------------------------------------
# Tests for load_previous_games
# ---------------------------------------------------------------------------

class TestLoadPreviousGames:
    def test_returns_empty_list_when_file_not_exists(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        with patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result == []

    def test_loads_valid_json_file(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with open(path, "w") as f:
            json.dump(sample_games, f)
        with patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result == sample_games

    def test_returns_empty_list_on_corrupted_json(self, tmp_path):
        path = str(tmp_path / "games.json")
        with open(path, "w") as f:
            f.write("this is not valid json {{{{")
        with patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result == []

    def test_returns_empty_list_when_data_is_not_a_list(self, tmp_path):
        path = str(tmp_path / "games.json")
        with open(path, "w") as f:
            json.dump({"key": "value"}, f)
        with patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result == []

    def test_returns_empty_list_when_items_are_not_dicts(self, tmp_path):
        path = str(tmp_path / "games.json")
        with open(path, "w") as f:
            json.dump(["game1", "game2"], f)
        with patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result == []

    def test_returns_empty_list_on_io_error(self, tmp_path):
        path = str(tmp_path / "games.json")
        (tmp_path / "games.json").write_text("[]")
        with patch("modules.storage.DATA_FILE_PATH", path), \
             patch("builtins.open", side_effect=IOError("disk read error")):
            result = storage.load_previous_games()
        assert result == []

    def test_loaded_games_preserve_all_fields(self, tmp_path, sample_game):
        path = str(tmp_path / "games.json")
        with open(path, "w") as f:
            json.dump([sample_game], f)
        with patch("modules.storage.DATA_FILE_PATH", path):
            result = storage.load_previous_games()
        assert result[0]["title"] == sample_game["title"]
        assert result[0]["link"] == sample_game["link"]
        assert result[0]["end_date"] == sample_game["end_date"]
        assert result[0]["description"] == sample_game["description"]
        assert result[0]["thumbnail"] == sample_game["thumbnail"]


# ---------------------------------------------------------------------------
# Tests for save_games
# ---------------------------------------------------------------------------

class TestSaveGames:
    def test_saves_games_to_file(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with patch("modules.storage.DATA_FILE_PATH", path):
            storage.save_games(sample_games)
        with open(path, "r") as f:
            saved = json.load(f)
        assert saved == sample_games

    def test_does_not_write_when_games_is_empty(self, tmp_path):
        path = str(tmp_path / "games.json")
        with patch("modules.storage.DATA_FILE_PATH", path):
            storage.save_games([])
        assert not os.path.exists(path)

    def test_creates_directory_if_missing(self, tmp_path, sample_games):
        sub_dir = tmp_path / "nested" / "dir"
        path = str(sub_dir / "games.json")
        with patch("modules.storage.DATA_FILE_PATH", path):
            storage.save_games(sample_games)
        assert os.path.exists(path)

    def test_raises_io_error_on_permission_error(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with patch("modules.storage.DATA_FILE_PATH", path), \
             patch("builtins.open", side_effect=PermissionError("denied")):
            with pytest.raises(IOError):
                storage.save_games(sample_games)

    def test_raises_type_error_on_unserializable_data(self, tmp_path):
        path = str(tmp_path / "games.json")
        games = [{"title": object()}]  # object() is not JSON-serialisable
        with patch("modules.storage.DATA_FILE_PATH", path):
            with pytest.raises(TypeError):
                storage.save_games(games)

    def test_saved_file_is_valid_json(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with patch("modules.storage.DATA_FILE_PATH", path):
            storage.save_games(sample_games)
        with open(path, "r") as f:
            content = f.read()
        parsed = json.loads(content)
        assert isinstance(parsed, list)

    def test_save_then_load_round_trip(self, tmp_path, sample_games):
        path = str(tmp_path / "games.json")
        with patch("modules.storage.DATA_FILE_PATH", path):
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
            json.dump(sample_games, f)
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
        assert saved == sample_games
