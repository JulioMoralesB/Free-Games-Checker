from config import DISCORD_WEBHOOK_URL, TIMEZONE, LOCALE, DATE_FORMAT, EPIC_GAMES_REGION
import requests
from datetime import datetime
import pytz
import locale
from urllib.parse import urlparse

import logging
logger = logging.getLogger(__name__)

if LOCALE:
    try:
        locale.setlocale(locale.LC_TIME, LOCALE)
    except locale.Error as exc:
        logger.warning(
            "Locale %s is not available, falling back to system locale. "
            "Date formatting may differ. Underlying error: %s",
            LOCALE,
            exc,
            exc_info=True,
        )

def _get_safe_webhook_identifier(webhook_url: str) -> str:
    """
    Return a redacted identifier for a webhook URL that is safe to log.
    For Discord webhooks, this will be `<host>/api/webhooks/<id>` (no token).
    For other URLs, this falls back to the hostname or a generic placeholder.
    """
    if not webhook_url:
        return "unknown-webhook"
    try:
        parsed = urlparse(webhook_url)
        host = parsed.netloc or "unknown-host"
        path = parsed.path or ""

        # Expected Discord webhook pattern: /api/webhooks/<id>/<token>
        segments = path.strip("/").split("/")
        if len(segments) >= 3 and segments[0] == "api" and segments[1] == "webhooks":
            webhook_id = segments[2]
            return f"{host}/api/webhooks/{webhook_id}"

        # Fallback: only host if path does not match expected pattern
        return host
    except Exception:
        # In case of any parsing error, avoid logging the raw URL
        return "invalid-webhook-url"

def send_discord_message(new_games):
    """
    Send a Discord webhook message for new free games.
    
    Args:
        new_games: List of game dictionaries to send to Discord
        
    Raises:
        ValueError: If webhook URL is not configured
        requests.RequestException: If the HTTP request fails
    """
    if not DISCORD_WEBHOOK_URL:
        error_msg = "Discord webhook URL not configured in environment variables"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        embeds = []
        for game in new_games:
            try:
                end_date = datetime.strptime(game["end_date"], "%Y-%m-%dT%H:%M:%S.%fZ")

                dt_obj = pytz.utc.localize(end_date)
                try:
                    configured_tz = pytz.timezone(TIMEZONE)
                except pytz.exceptions.UnknownTimeZoneError:
                    logger.warning(
                        "Unknown timezone %r — falling back to UTC. "
                        "Set a valid IANA timezone in the TIMEZONE environment variable.",
                        TIMEZONE,
                    )
                    configured_tz = pytz.utc
                localized_end_date = dt_obj.astimezone(configured_tz)

                # Compute UTC offset dynamically from the localized date (e.g. "UTC+05:30")
                tz_offset_str = localized_end_date.strftime("%z")  # e.g. "-0600" or "+0530"
                if tz_offset_str and len(tz_offset_str) == 5:
                    sign = "+" if tz_offset_str[0] == "+" else "-"
                    hours = tz_offset_str[1:3]
                    minutes = tz_offset_str[3:5]
                    utc_label = f"UTC{sign}{hours}:{minutes}"
                else:
                    utc_label = "UTC"

                # Format the final string, including the timezone name for context
                formatted_end_date = f"{localized_end_date.strftime(DATE_FORMAT)} {utc_label} ({TIMEZONE})"
                embeds.append(
                    {
                        "author": {
                            "name": "Epic Games Store",
                            "url": f"https://store.epicgames.com/{EPIC_GAMES_REGION}/free-games"
                        },
                        "title": game["title"],
                        "url": game["link"],
                        "description": game["description"].replace("'", ""),
                        "color": 0x2ECC71,
                        "image": {
                            "url": game["thumbnail"]
                        },
                        "footer": {
                            "text": f"Finaliza el {formatted_end_date}"
                        }
                    }
                )
            except (KeyError, ValueError) as e:
                logger.error(f"Error processing game data for embed: {str(e)} | Game data: {game}")
                raise
            
        data = {
            "content": "**Nuevo Juego Gratis en Epic Games Store! 🎮**\n",
            "embeds": embeds
        }
        logger.info(f"Sending Discord message with {len(embeds)} game(s)")

        safe_webhook_id = _get_safe_webhook_identifier(DISCORD_WEBHOOK_URL)
        
        # Send the request and validate response
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
        
        # Validate HTTP response status (200-299 range)
        if 200 <= response.status_code <= 299:
            logger.info(f"Discord message sent successfully (Status: {response.status_code})")
        else:
            error_context = {
                "status_code": response.status_code,
                "webhook_url_pattern": safe_webhook_id,
                "response_text": response.text[:200],  # Limit response text for logging
                "num_games": len(new_games)
            }
            logger.error(f"Discord API returned non-success status: {error_context}")
            response.raise_for_status()  # Raise exception for bad status codes
            
    except requests.exceptions.Timeout as e:
        safe_webhook_id = _get_safe_webhook_identifier(DISCORD_WEBHOOK_URL)
        logger.error(
            f"Discord request timed out after 10 seconds | Webhook identifier: {safe_webhook_id} | Games: {len(new_games)}"
        )
        raise
    except requests.exceptions.ConnectionError as e:
        safe_webhook_id = _get_safe_webhook_identifier(DISCORD_WEBHOOK_URL)
        logger.error(
            f"Discord connection error: {str(e)} | Webhook identifier: {safe_webhook_id} | Games: {len(new_games)}"
        )
        raise
    except requests.exceptions.RequestException as e:
        safe_webhook_id = _get_safe_webhook_identifier(DISCORD_WEBHOOK_URL)
        logger.error(
            f"Discord request failed: {str(e)} | Webhook identifier: {safe_webhook_id} | Games: {len(new_games)}"
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending Discord message: {str(e)} | Games: {len(new_games)}")
        raise
    
