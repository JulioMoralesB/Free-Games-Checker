from config import DISCORD_WEBHOOK_URL
import requests
from datetime import datetime
import pytz
import locale
from urllib.parse import urlparse

import logging
logger = logging.getLogger(__name__)

try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error as exc:
    logger.warning(
        "Locale es_ES.UTF-8 is not available, falling back to system locale. "
        "Date formatting may differ. Underlying error: %s",
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
                mexico_tz = pytz.timezone("America/Mexico_City")
                localized_end_date = dt_obj.astimezone(mexico_tz)

                # Format date manually, check if AM or PM, since %p may not work in some systems
                hour = int(localized_end_date.strftime("%H"))

                if hour >= 12:
                    am_pm_text = "PM"
                else:
                    am_pm_text = "AM"

                # Format the final string
                formatted_end_date = f"{localized_end_date.strftime('%d de %B de %Y a las %I:%M')} {am_pm_text} UTC-6 (Hora de México)"
                embeds.append(
                    {
                        "author": {
                            "name": "Epic Games Store",
                            "url": "https://store.epicgames.com/es-MX/free-games"
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
    
