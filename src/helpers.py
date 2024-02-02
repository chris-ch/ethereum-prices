
import logging
import os
from typing import Optional
import requests
import json


def setup_logging_levels():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')


def notify_slack(message: str) -> Optional[requests.Response]:
    url = os.environ["SLACK_WEBHOOK_URL"]
    if not url:
        logging.warning("missing environment variable SLACK_WEBHOOK_URL")
        return None

    payload = {"text": message}
    headers = {"Content-type": "application/json"}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response
