
import io
import logging
import os
from typing import Optional
import requests
import json

import botocore.exceptions


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


def fetch_object(s3, bucket_name: str, filename: str) -> Optional[io.BytesIO]:
    try:
        data = io.BytesIO()
        s3.Object(bucket_name, filename).download_fileobj(data)
        return data
    except botocore.exceptions.ClientError as ce:
        logging.error(f"failed to load {bucket_name}:{filename}", ce)
        return None
