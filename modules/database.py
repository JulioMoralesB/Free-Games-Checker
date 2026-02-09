import psycopg2
from psycopg2 import sql

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
                    cursor.execute("SET search_path to free_games")

                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS games (
                            id SERIAL PRIMARY KEY,
                            game_id VARCHAR(255) UNIQUE NOT NULL,
                            title TEXT NOT NULL,
                            link TEXT NOT NULL,
                            description TEXT,
                            thumbnail TEXT,
                            promotion_end_date TIMESTAMP
                        )
                    """)
                    conn.commit()
                    logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def insert_game(self, game):
        """Insert a game record into the database."""
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cursor:
                    
                    # Set schema for this connection
                    cursor.execute("SET search_path to free_games")

                    cursor.execute("""
                        INSERT INTO games (game_id, title, link, description, thumbnail, promotion_end_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
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