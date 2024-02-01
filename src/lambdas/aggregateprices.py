import asyncio
import logging
import os

import binanceprices

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    bucket_name = os.environ["BUCKET_BINANCE_PRICES"]
    instrument_code = event["instrument_code"]
    count_years = event["count_years"]
    logging.info(f"processing event: {event}")
    df = binanceprices.load_prices(bucket_name, instrument_code, count_years)
    return { 
        'message' : f"loaded {df.index.size} rows"
    }
