import requests
from config import HEALTHCHECK_URL

import logging

logger = logging.getLogger(__name__)

# Sends a hearthbeat to a monitor service like UptimeKuma to ensure that the service is running and healthy
def healthcheck():
    logger.info(f"Sending request to healtcheck monitor. URL: {HEALTHCHECK_URL}")
    response = requests.get(HEALTHCHECK_URL)
    logger.info(f"Received response from monitor. Status Code: {response.status_code}")
    logger.info(f"Response content: {response.text}")
    if response.status_code != 200 or response.text.strip().lower() != "ok":
        logger.error(f"Failed to get response from monitor. Status Code: {response.status_code}")
        return
    logger.info("Obtained 200 status code from monitor response. Service is healthty")