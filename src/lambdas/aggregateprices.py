import logging

import binanceprices

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    bucket_name = event["bucket_name"]
    instrument_code = event["instrument_code"]
    count_years = event["count_years"]
    logging.info(f"processing event: {event}")
    df = binanceprices.load_prices(bucket_name, instrument_code, count_years)
    return { 
        'message' : f"loaded {df.index.count} rows"
    }
