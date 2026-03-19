from config import DISCORD_WEBHOOK_URL
import requests
from datetime import datetime
import pytz
import locale

locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

import logging
logger = logging.getLogger(__name__)

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
                formated_end_date = f"{localized_end_date.strftime('%d de %B de %Y a las %I:%M')} {am_pm_text} UTC-6 (Hora de México)"
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
                            "text": f"Finaliza el {formated_end_date}"
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
        
        # Send the request and validate response
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
        
        # Validate HTTP response status (200-299 range)
        if 200 <= response.status_code <= 299:
            logger.info(f"Discord message sent successfully (Status: {response.status_code})")
        else:
            error_context = {
                "status_code": response.status_code,
                "webhook_url_pattern": DISCORD_WEBHOOK_URL[:20] + "..." if len(DISCORD_WEBHOOK_URL) > 20 else DISCORD_WEBHOOK_URL,
                "response_text": response.text[:200],  # Limit response text for logging
                "num_games": len(new_games)
            }
            logger.error(f"Discord API returned non-success status: {error_context}")
            response.raise_for_status()  # Raise exception for bad status codes
            
    except requests.exceptions.Timeout as e:
        logger.error(f"Discord request timed out after 10 seconds | Webhook URL pattern: {DISCORD_WEBHOOK_URL[:20]}... | Games: {len(new_games)}")
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Discord connection error: {str(e)} | Webhook URL pattern: {DISCORD_WEBHOOK_URL[:20]}... | Games: {len(new_games)}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Discord request failed: {str(e)} | Webhook URL pattern: {DISCORD_WEBHOOK_URL[:20]}... | Games: {len(new_games)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending Discord message: {str(e)} | Games: {len(new_games)}")
        raise
    
