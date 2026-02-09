from datetime import datetime

from modules.notifier import send_discord_message
from modules.scrapper import fetch_free_games
from modules.storage import load_previous_games, save_games
from modules.healthcheck import healthcheck
from modules.database import FreeGamesDatabase

import schedule
import time

import logging
from logging.handlers import TimedRotatingFileHandler

# Configure logging to write to a file and rotate weekly
log_handler = TimedRotatingFileHandler("/mnt/logs/checker.log", when="W1", interval=1, backupCount=4)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(level=logging.INFO, handlers=[log_handler, console_handler])

def check_games():
    
    """Main execution function."""
    logging.info("Checking for new free games...")

    current_games = fetch_free_games()
    logging.info(f"Games obtained from scrapper.py: {current_games}")
    if current_games == []:
        logging.error("No free games found or failed to fetch.")
        return

    previous_games = load_previous_games()
    logging.debug(f"Previous games loaded from storage: {previous_games}")
    new_games = [game for game in current_games if game not in previous_games]

    if new_games:
        logging.info(f"Found {len(new_games)} new free games! Sending notification...")
        send_discord_message(new_games)
        save_games(current_games)
    else:
        logging.warning("No new free games detected.")

def main():
    db = FreeGamesDatabase()
    db.init_db()
    check_games()
    healthcheck()

    logging.debug("Starting scheduler...")

    schedule.every().day.at("12:00").do(check_games)
    schedule.every().minute.do(healthcheck)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    logging.info("Starting service...")
    main()
