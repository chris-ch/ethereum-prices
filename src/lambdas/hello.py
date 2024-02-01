import pandas
import binanceprices
import boto3

def handler(event, context):
    df = binanceprices.load_prices("prod-binance-prices", "ETHUSDT", 6)
    return { 
        'message' : f"loaded {df.index.count} rows"
    }
