import binance
from datetime import datetime, timedelta
import pandas
from data_cache import pandas_cache

COUNT_YEARS = 10
BINANCE_DATETIME_FORMAT = "%Y-%m-%d %H-%M-%S"


@pandas_cache("code", "year")
def load_prices(client: binance.Client, code: str, year: int):
    from_date = datetime(year, 1, 1, 0, 0, 0)
    until_date = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)

    # Execute the query from binance - timestamps must be converted to strings !
    candles = client.get_historical_klines(code, binance.Client.KLINE_INTERVAL_1HOUR, str(from_date), str(until_date))

    # Create a dataframe to label all the columns returned by binance so we work with them later.
    df = pandas.DataFrame(candles, columns=['dateTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime',
                                           'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol',
                                           'ignore'])

    # as timestamp is returned in ms, let us convert this back to proper timestamps.
    df.dateTime = pandas.to_datetime(df.dateTime, unit='ms').dt.strftime(BINANCE_DATETIME_FORMAT)
    df.set_index('dateTime', inplace=True)
    return df


def main():
    # Create a client object
    client = binance.Client()

    current_year = datetime.now().year
    df_years = list()
    for year in range(current_year - COUNT_YEARS, current_year):
        df = load_prices(client, "ETHUSDT", year)
        df = df.drop(['closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'], axis=1)
        df_years.append(df)

    output_df = pandas.concat(df_years, axis=0)
    print(output_df)


if __name__ == '__main__':
    main()