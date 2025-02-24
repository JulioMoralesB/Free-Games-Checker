import json
import os

from config import DATA_FILE_PATH

def load_previous_games():
    """Load the last known free games from file."""
    if os.path.exists(DATA_FILE_PATH):
        with open(DATA_FILE_PATH, "r") as file:
            return json.load(file)
    return []

def save_games(games):
    """Save the current free games list to file."""
    with open(DATA_FILE_PATH, "w") as file:
        json.dump(games, file, indent=4)