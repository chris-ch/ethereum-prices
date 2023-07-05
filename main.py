import os
from binance.client import Client
import pandas as pd
import datetime, time

COUNT_YEARS = 10

# Calculate the timestamps for the binance api function
untilThisDate = datetime.datetime.now()
sinceThisDate = untilThisDate - datetime.timedelta(days = 365 * COUNT_YEARS)

# Create a client object
client = Client()

# Execute the query from binance - timestamps must be converted to strings !
candle = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_1HOUR, str(sinceThisDate), str(untilThisDate))

# Create a dataframe to label all the columns returned by binance so we work with them later.
df = pd.DataFrame(candle, columns=['dateTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'])

# as timestamp is returned in ms, let us convert this back to proper timestamps.
df.dateTime = pd.to_datetime(df.dateTime, unit='ms').dt.strftime(Constants.DateTimeFormat)
df.set_index('dateTime', inplace=True)

# Get rid of columns we do not need
df = df.drop(['closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol','takerBuyQuoteVol', 'ignore'], axis=1)

print(df)