import requests
from config import HEALTHCHECK_URL

import logging

logger = logging.getLogger(__name__)


def healthcheck():
    logger.info("Sending request to healtcheck monitor")
    response = requests.get(HEALTHCHECK_URL)
    if response.status_code != 200:
        logger.error(f"Failed to get response from monitor. Status Code: {response.status_code}")
        return
    logger.info("Obtained 200 status code from monitor response. Service is healthty")