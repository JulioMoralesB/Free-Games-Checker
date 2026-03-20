import psycopg2

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

import logging
logger = logging.getLogger(__name__)

class FreeGamesDatabase:
    def __init__(self):
        self.conn_params = {
            "host": DB_HOST,
            "port": DB_PORT,
            "dbname": DB_NAME,
            "user": DB_USER,
            "password": DB_PASSWORD
        }

    def init_db(self):
        """Initialize the database by creating the necessary tables."""
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cursor:
                    
                    # Set schema for this connection
                    cursor.execute("SET search_path TO free_games")

                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS games (
                            id SERIAL PRIMARY KEY,
                            game_id VARCHAR(255) UNIQUE NOT NULL,
                            title TEXT NOT NULL,
                            link TEXT NOT NULL,
                            description TEXT,
                            thumbnail TEXT,
                            promotion_end_date TEXT
                        )
                    """)
                    conn.commit()
                    logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def get_games(self):
        """Retrieve all stored games from the database as a list of dicts."""
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET search_path TO free_games")
                    cursor.execute(
                        "SELECT title, link, description, thumbnail, promotion_end_date FROM games"
                    )
                    rows = cursor.fetchall()
                    games = [
                        {
                            "title": title,
                            "link": link,
                            "description": description or "",
                            "thumbnail": thumbnail or "",
                            "end_date": end_date or "",
                        }
                        for title, link, description, thumbnail, end_date in rows
                    ]
                    logger.debug(f"Retrieved {len(games)} games from database.")
                    return games
        except Exception as e:
            logger.error(f"Failed to retrieve games from database: {e}")
            raise

    def save_games(self, games):
        """Save games to the database, ignoring duplicates based on game_id (link)."""
        if not games:
            logger.warning("Attempted to save empty games list to database")
            return
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET search_path TO free_games")
                    for game in games:
                        # Use the full link as a stable unique identifier
                        game_id = game.get("link", "")
                        cursor.execute(
                            """
                            INSERT INTO games (game_id, title, link, description, thumbnail, promotion_end_date)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (game_id) DO NOTHING
                            """,
                            (
                                game_id,
                                game.get("title", ""),
                                game.get("link", ""),
                                game.get("description", ""),
                                game.get("thumbnail", ""),
                                game.get("end_date") or None,
                            ),
                        )
                    conn.commit()
                    logger.info(f"Saved {len(games)} games to database.")
        except Exception as e:
            logger.error(f"Failed to save games to database: {e}")
            raise
    
    def insert_game(self, game):
        """Insert a game record into the database."""
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cursor:
                    
                    # Set schema for this connection
                    cursor.execute("SET search_path to free_games")

                    cursor.execute("""
                        INSERT INTO games (game_id, title, link, description, thumbnail, promotion_end_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (game_id) DO NOTHING
                    """, (
                        game['game_id'],
                        game['title'],
                        game['link'],
                        game['description'],
                        game['thumbnail'],
                        game['end_date']
                    ))
                    conn.commit()
                    logger.info(f"Game '{game['title']}' inserted successfully.")
        except Exception as e:
            logger.error(f"Failed to insert game '{game['title']}': {e}")

    def get_all_games(self):
        """Retrieve all game records from the database."""
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cursor:
                    
                    # Set schema for this connection
                    cursor.execute("SET search_path to free_games")

                    cursor.execute("SELECT * FROM games")
                    games = cursor.fetchall()
                    logger.info(f"Retrieved {len(games)} games from the database.")
                    return games
        except Exception as e:
            logger.error(f"Failed to retrieve games: {e}")
            return []
    
    def game_exists(self, game_id):
        """Check if a game with the given game_id already exists in the database."""
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cursor:
                    
                    # Set schema for this connection
                    cursor.execute("SET search_path to free_games")

                    cursor.execute("SELECT 1 FROM games WHERE game_id = %s", (game_id,))
                    exists = cursor.fetchone() is not None
                    logger.debug(f"Game with ID '{game_id}' exists: {exists}")
                    return exists
        except Exception as e:
            logger.error(f"Failed to check if game exists: {e}")
            return False