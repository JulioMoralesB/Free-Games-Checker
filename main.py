from datetime import datetime, timezone

from modules.notifier import send_discord_message
from modules.scrapers import EpicGamesScraper
from modules.storage import load_previous_games, save_games, save_last_notification
from modules.healthcheck import healthcheck
from modules.database import FreeGamesDatabase
from config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    SCHEDULE_TIME,
    HEALTHCHECK_INTERVAL,
    TIMEZONE,
    API_HOST,
    API_PORT,
)

import os
import schedule
import time
import threading
import requests
import psycopg2

from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

import logging
from logging.handlers import TimedRotatingFileHandler
import pytz

# Custom formatter to display log timestamps in the configured timezone instead of UTC
class TimezoneFormatter(logging.Formatter):
    def __init__(self, fmt, tz):
        super().__init__(fmt)
        try:
            self.tz = pytz.timezone(tz)
        except pytz.exceptions.UnknownTimeZoneError:
            logging.warning(
                "Timezone %s is not available, falling back to UTC. "
                "Log timestamps will be in UTC. "
                "Check the TIMEZONE environment variable.",
                tz,
            )
            self.tz = pytz.utc

    def converter(self, timestamp):
        return datetime.fromtimestamp(timestamp, tz=pytz.utc).astimezone(self.tz).timetuple()

# Configure logging to write to a file and rotate weekly
log_handler = TimedRotatingFileHandler("/mnt/logs/notifier.log", when="W1", interval=1, backupCount=4)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(TimezoneFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', tz=TIMEZONE))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(TimezoneFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', tz=TIMEZONE))

logging.basicConfig(level=logging.INFO, handlers=[log_handler, console_handler])


def _find_new_games(current_games, previous_games):
    """Return games that are newly free compared to still-active previous promos."""

    def _is_still_active(previous_game):
        end_date = previous_game.end_date
        if not end_date:
            # Treat unknown end dates as active to avoid duplicate notifications.
            return True

        normalized = end_date.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        try:
            ends_at = datetime.fromisoformat(normalized)
        except ValueError:
            # Keep legacy/malformed records from causing false "new" alerts.
            return True

        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)

        return ends_at >= datetime.now(timezone.utc)

    # A (url, end_date) pair that already appeared in previous games should not
    # trigger a new notification, regardless of whether the promo is still active.
    # This prevents re-notifying for the same expired promo while still allowing
    # re-notification when the same game has a new promo (different end_date).
    previous_seen = {
        (game.url, game.end_date)
        for game in previous_games
        if game.url
    }

    # Also track active URLs to suppress games seen before whose promos are still running.
    previous_active_urls = {
        game.url
        for game in previous_games
        if game.url and _is_still_active(game)
    }

    new_games = []
    for game in current_games:
        url = game.url
        if url:
            if url not in previous_active_urls and (url, game.end_date) not in previous_seen:
                new_games.append(game)
            continue

        # Fallback for malformed records that do not have a url.
        if game not in previous_games:
            new_games.append(game)

    return new_games

def check_games():
    
    """Main execution function that checks for new free games and sends Discord notification."""
    logging.info("Checking for new free games...")

    try:
        scraper = EpicGamesScraper()
        current_games = scraper.fetch_free_games()
        logging.info(f"Games obtained from scraper: {len(current_games)} game(s)")
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

    new_games = _find_new_games(current_games, previous_games)

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

        # Persist the last notification batch so the resend endpoint can replay it
        try:
            save_last_notification(new_games)
        except Exception as e:
            logging.error(f"Failed to save last notification: {str(e)}")
            logging.warning("Discord notification was sent but failed to record it for the resend endpoint.")

    else:
        logging.warning("No new free games detected.")

    # Always persist current_games so that the DB upsert keeps end_date values
    # fresh, preventing stale promos from triggering false re-notifications.
    try:
        save_games(current_games)
        logging.info("Games saved successfully to storage")
    except IOError as e:
        logging.error(f"Failed to save games to storage: {str(e)}")
        logging.warning("Failed to update local cache. This may cause duplicate notifications next run.")
    except Exception as e:
        logging.error(f"Unexpected error saving games: {str(e)}")
        logging.warning("Failed to update local cache.")

def _run_db_migrations():
    """Apply any pending Alembic migrations up to the latest revision."""
    logging.info("Applying database migrations...")
    # Suppress verbose per-revision Alembic log lines from service logs.
    # env.py skips fileConfig when the service's logging is already configured,
    # but raise the level here as well to guard against any propagation.
    logging.getLogger("alembic").setLevel(logging.WARNING)
    cfg = AlembicConfig(os.path.join(os.path.dirname(__file__), "alembic.ini"))
    alembic_command.upgrade(cfg, "head")
    logging.info("Database migrations applied successfully.")


def _verify_required_tables():
    """Fail fast when required DB tables are missing after migrations."""
    logging.info("Verifying required database tables...")

    conn_params = {
        "host": DB_HOST,
        "port": DB_PORT,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT to_regclass('free_games.last_notification')")
            if cursor.fetchone()[0] is None:
                raise RuntimeError(
                    "Required table free_games.last_notification is missing after migrations. "
                    "Run 'alembic upgrade head' and verify DB permissions."
                )

    logging.info("Required database tables verified successfully.")


def _start_api_server():
    """Start the FastAPI server in a background daemon thread."""
    import uvicorn
    from api import app

    logging.info("Starting REST API server on %s:%s...", API_HOST, API_PORT)
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="info")


def main():
    if DB_HOST:
        logging.info("Database configuration detected. Initializing database...")
        db = FreeGamesDatabase()
        db.init_db()
        _run_db_migrations()
        _verify_required_tables()
    else:
        logging.info("No database configuration detected. Using JSON file storage.")

    # Start REST API server in a background thread
    api_thread = threading.Thread(target=_start_api_server, daemon=True)
    api_thread.start()

    check_games()
    healthcheck()

    logging.debug("Starting scheduler...")

    schedule.every().day.at(SCHEDULE_TIME, tz=TIMEZONE).do(check_games)
    schedule.every(HEALTHCHECK_INTERVAL).minutes.do(healthcheck)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    logging.info("Starting service...")
    main()
