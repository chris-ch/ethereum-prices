import boto3
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

    s3 = boto3.resource('s3')
    df = binanceprices.load_prices(s3, bucket_name, instrument_code, count_years)
    target_filename = f'{instrument_code}-full.csv.zip'
    binanceprices.create_file(s3, bucket_name, target_filename, df)
    # notify slack
    return { 
        'message' : f"loaded {df.index.size} rows"
    }
