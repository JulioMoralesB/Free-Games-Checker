import json
import os
import logging

from config import DATA_FILE_PATH, DB_HOST

logger = logging.getLogger(__name__)


def _is_db_configured():
    """Return True when PostgreSQL connection parameters are available."""
    return bool(DB_HOST)


# ---------------------------------------------------------------------------
# Public interface (used by main.py)
# ---------------------------------------------------------------------------

def load_previous_games():
    """
    Load the last known free games from the configured storage backend.

    Uses PostgreSQL when DB_HOST is set, otherwise falls back to the JSON file.

    Returns:
        list: Previously saved games, or empty list on error / first run.
    """
    if _is_db_configured():
        return _load_from_db()
    return _load_from_file()


def save_games(games):
    """
    Save the current free games list to the configured storage backend.

    Uses PostgreSQL when DB_HOST is set, otherwise falls back to the JSON file.

    Args:
        games: List of game dictionaries to save.

    Raises:
        IOError: If the save operation fails.
        TypeError: If games data cannot be serialised (file backend only).
    """
    if _is_db_configured():
        _save_to_db(games)
    else:
        _save_to_file(games)


# ---------------------------------------------------------------------------
# PostgreSQL backend
# ---------------------------------------------------------------------------

def _load_from_db():
    from modules.database import FreeGamesDatabase
    try:
        db = FreeGamesDatabase()
        games = db.get_games()
        logger.debug(f"Loaded {len(games)} previous games from database.")
        return games
    except Exception as e:
        logger.error(f"Failed to load games from database: {e}")
        return []


def _save_to_db(games):
    from modules.database import FreeGamesDatabase
    if not games:
        logger.warning("Attempted to save empty games list")
        return
    try:
        db = FreeGamesDatabase()
        db.save_games(games)
    except Exception as e:
        logger.error(f"Failed to save games to database: {e}")
        raise IOError("Failed to save games to database") from e


# ---------------------------------------------------------------------------
# JSON file backend (development / fallback when DB_HOST is not set)
# ---------------------------------------------------------------------------

def _load_from_file():
    """
    Load the last known free games from file.

    Returns:
        list: Previously saved games, or empty list if file doesn't exist or is corrupted.
    """
    if not os.path.exists(DATA_FILE_PATH):
        logger.debug(f"Data file does not exist yet: {DATA_FILE_PATH}")
        return []

    try:
        with open(DATA_FILE_PATH, "r") as file:
            data = json.load(file)

            # Validate that the loaded data is a list of game dictionaries
            if not isinstance(data, list):
                logger.error(
                    f"Unexpected JSON structure in data file: expected list, got {type(data).__name__} | "
                    f"File path: {DATA_FILE_PATH}"
                )
                logger.warning("Returning empty list due to invalid JSON structure to prevent incorrect processing.")
                return []

            if not all(isinstance(game, dict) for game in data):
                logger.error(
                    f"Unexpected item types in games list from data file. "
                    f"Expected list of dicts. File path: {DATA_FILE_PATH}"
                )
                logger.warning("Returning empty list due to invalid game entries to prevent incorrect processing.")
                return []

            logger.debug(f"Successfully loaded {len(data)} previous games from {DATA_FILE_PATH}")
            return data
    except FileNotFoundError:
        logger.error(f"Data file not found when attempting to read: {DATA_FILE_PATH}")
        return []
    except IOError as e:
        logger.error(f"I/O error reading data file: {str(e)} | File path: {DATA_FILE_PATH}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in data file: {str(e)} | File path: {DATA_FILE_PATH} | Line: {e.lineno}, Column: {e.colno}")
        logger.warning("Returning empty list to prevent scheduler crash. File may be corrupted.")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading previous games: {str(e)} | File path: {DATA_FILE_PATH}")
        return []


def _save_to_file(games):
    """
    Save the current free games list to file.

    Args:
        games: List of game dictionaries to save.

    Raises:
        IOError: If file write fails due to I/O issues.
        TypeError: If games data cannot be serialized to JSON.
    """
    if not games:
        logger.warning("Attempted to save empty games list")
        return

    try:
        # Ensure directory exists
        directory = os.path.dirname(DATA_FILE_PATH)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Created directory: {directory}")

        with open(DATA_FILE_PATH, "w") as file:
            json.dump(games, file, indent=4)
            logger.info(f"Successfully saved {len(games)} games to {DATA_FILE_PATH}")

    except PermissionError as e:
        logger.error(f"Permission denied writing to data file: {str(e)} | File path: {DATA_FILE_PATH}")
        logger.warning("File save failed due to permission issues. Scheduler will continue.")
        raise IOError(f"Permission denied saving games to {DATA_FILE_PATH}") from e
    except IOError as e:
        logger.error(f"I/O error writing data file: {str(e)} | File path: {DATA_FILE_PATH}")
        logger.warning("File save failed. Scheduler will continue.")
        raise
    except TypeError as e:
        logger.error(f"JSON serialization error: {str(e)} | Games data type: {type(games)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error saving games: {str(e)} | File path: {DATA_FILE_PATH}")
        raise IOError(f"Unexpected error saving games") from e