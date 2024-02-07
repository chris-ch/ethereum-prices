import time
import hashlib
import hmac
import json
import os
import logging

import requests
from requests import auth

import helpers

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_bearer_token(auth_url: str, api_key: str, api_secret: str):
    logging.info(f"calling {auth_url}")
    data = {
        'grant_type': 'client_credentials',
        'client_id': api_key,
        'client_secret': api_secret
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.get(auth_url, headers=headers, params=data)
    token_data = response.json()
    return token_data.get('result', {}).get('access_token', None)


def get_account_summary(account_summary_url: str, bearer_token: str, currency: str):
    data = {
        'currency': currency,
        'extended': 'true'
    }
    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(account_summary_url, headers=headers, params=data)
    return response.json()


def handler(event, context):
    api_key = os.environ["DERIBIT_CLIENT_ID"]
    api_secret = os.environ["DERIBIT_CLIENT_SECRET"]
    base_url = "https://www.deribit.com/api/v2"
    private_url = f"{base_url}/private"
    public_url = f"{base_url}/public"
    currency = event["currency"]
    auth_url = f"{public_url}/auth"
    account_summary_url = f"{private_url}/get_account_summary"

    bearer_token = get_bearer_token(auth_url, api_key, api_secret)
    if not bearer_token:
        raise ValueError("failed to authenticate")
 
    account_summary = get_account_summary(account_summary_url, bearer_token, currency)
    
    message = f"""{account_summary}"""
    helpers.notify_slack(message)
    return { 
        'message' : account_summary
    }
