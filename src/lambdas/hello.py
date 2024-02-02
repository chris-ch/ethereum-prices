import binanceprices
import boto3

def handler(event, context):
    s3 = boto3.resource('s3')
    df = binanceprices.load_prices(s3, "prod-binance-prices", "ETHUSDT", 6, no_update=True)
    return { 
        'message' : f"loaded {df.index.count} rows"
    }
