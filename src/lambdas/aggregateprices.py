import boto3
import logging
import os

import binanceprices
import helpers

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    bucket_name = os.environ["BUCKET_BINANCE_PRICES"]
    no_update = os.getenv("BINANCE_PRICES_UPDATE", default='False').lower() == 'true'
    instrument_code = event["instrument_code"]
    count_years = event["count_years"]
    logging.info(f"processing event: {event}")

    s3 = boto3.resource('s3')
    df = binanceprices.load_prices(s3, bucket_name, instrument_code, count_years, no_update=no_update)
    target_filename = f'{instrument_code}-full.csv.zip'
    binanceprices.create_file(s3, bucket_name, target_filename, df)
    message = f"saved {target_filename} to bucket {bucket_name} ({df.index.size} rows)"
    helpers.notify_slack(message)
    return { 
        'message' : message
    }
