from datetime import datetime

from modules.notifier import send_discord_message
from modules.scrapper import fetch_free_games
from modules.storage import load_previous_games, save_games
from modules.healthcheck import healthcheck
from modules.database import FreeGamesDatabase
from config import DB_HOST, SCHEDULE_TIME, HEALTHCHECK_INTERVAL

import schedule
import time
import requests

import logging
from logging.handlers import TimedRotatingFileHandler

# Configure logging to write to a file and rotate weekly
log_handler = TimedRotatingFileHandler("/mnt/logs/notifier.log", when="W1", interval=1, backupCount=4)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(level=logging.INFO, handlers=[log_handler, console_handler])

def check_games():
    
    """Main execution function that checks for new free games and sends Discord notification."""
    logging.info("Checking for new free games...")

    try:
        current_games = fetch_free_games()
        logging.info(f"Games obtained from scrapper.py: {len(current_games)} game(s)")
    except Exception as e:
        logging.error(f"Failed to fetch games from scraper: {str(e)}")
        return

    if current_games == []:
        logging.error("No free games found or failed to fetch.")
        return

    try:
        previous_games = load_previous_games()
        logging.info(f"Previous games loaded from storage: {previous_games} game(s)")
    except Exception as e:
        logging.error(f"Failed to load previous games: {str(e)}")
        return

    new_games = [game for game in current_games if game not in previous_games]

    if new_games:
        logging.info(f"Found {len(new_games)} new free games! Sending Discord notification...")
        
        # Wrap Discord send with try-except to prevent scheduler crash
        try:
            send_discord_message(new_games)
            logging.info("Discord notification sent successfully")
        except ValueError as e:
            logging.error(f"Discord error (ValueError) while sending message: {str(e)}")
            logging.warning("Discord notification failed due to a ValueError, but continuing scheduler. Investigate the underlying cause (configuration or data-related).")
            # Don't save games if Discord notification fails
            return
        except requests.exceptions.RequestException as e:
            logging.error(f"Discord request failed (network/HTTP error): {str(e)} | Games to notify: {len(new_games)}")
            logging.warning("Discord notification failed due to network issue, but continuing scheduler.")
            # Don't save games if Discord notification fails
            return
        except Exception as e:
            logging.error(f"Unexpected error sending Discord message: {str(e)} | Games to notify: {len(new_games)}")
            logging.warning("Discord notification failed unexpectedly, but continuing scheduler.")
            # Don't save games if Discord notification fails
            return

        # Save games to storage after successful Discord notification
        try:
            save_games(current_games)
            logging.info(f"Games saved successfully after Discord notification")
        except IOError as e:
            logging.error(f"Failed to save games to storage: {str(e)}")
            logging.warning("Discord notification was sent but failed to update local cache. This may cause duplicate notifications next run.")
        except Exception as e:
            logging.error(f"Unexpected error saving games: {str(e)}")
            logging.warning("Discord notification was sent but failed to update local cache.")
    else:
        logging.warning("No new free games detected.")

def main():
    if DB_HOST:
        logging.info("Database configuration detected. Initializing database...")
        db = FreeGamesDatabase()
        db.init_db()
    else:
        logging.info("No database configuration detected. Using JSON file storage.")
    check_games()
    healthcheck()

    logging.debug("Starting scheduler...")

    schedule.every().day.at(SCHEDULE_TIME).do(check_games)
    schedule.every(HEALTHCHECK_INTERVAL).minutes.do(healthcheck)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    logging.info("Starting service...")
    main()
