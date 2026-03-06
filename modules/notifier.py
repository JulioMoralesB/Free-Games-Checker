from config import DISCORD_WEBHOOK_URL
import requests
from datetime import datetime
import pytz
import locale

locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

import logging
logger = logging.getLogger(__name__)

def send_discord_message(new_games):
    """Send a Discord webhook message."""
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook URL not set!")
        return
    embeds = []
    for game in new_games:
        
        end_date = datetime.strptime(game["end_date"], "%Y-%m-%dT%H:%M:%S.%fZ")

        dt_obj = pytz.utc.localize(end_date)
        mexico_tz = pytz.timezone("America/Mexico_City")
        localized_end_date = dt_obj.astimezone(mexico_tz)

        # Format date manually, check if AM or PM, since %p may not work in some systems
        hour = localized_end_date.strftime("%H")

        if hour >= "12":
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
        
    data = {
        "content": "**Nuevo Juego Gratis en Epic Games Store! 🎮**\n",
        "embeds": embeds
    }
    logger.info(f"Sending Discord message: {data}")
    requests.post(DISCORD_WEBHOOK_URL, json=data)
    
