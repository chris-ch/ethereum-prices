import os
from datetime import datetime, timedelta

import binance
import pandas


def first_day_of_next_month(year: int, month: int) -> datetime:
    """Returns the first datetime of the next month.

    Args:
    year: The year.
    month: The month.

    Returns:
    A datetime object representing the first day of the next month.
    """

    next_month = month + 1
    if next_month > 12:
        next_month = 1
        year += 1
    return datetime(year, next_month, 1)


def load_prices_by_month(path:str, code: str, year: int, month: int, force_refresh: bool = False) -> pandas.DataFrame:
    target_path = f'{path}/{code}/{year}'
    target_filename = f'{target_path}/{year}-{month:02d}.csv.zip'
    if os.path.exists(target_filename) and not force_refresh:
        binance_prices = pandas.read_csv(target_filename, compression='infer', header=0)
    else:
        print(f'no previous data found in {target_path}, loading from binance')
        binance_client = binance.Client()
        from_date = datetime(year, month, 1, 0, 0, 0)
        until_date = first_day_of_next_month(year, month) - timedelta(seconds=1)

        candles = binance_client.get_historical_klines(code, binance.Client.KLINE_INTERVAL_1HOUR, str(from_date),
                                                       str(until_date))
        binance_prices = pandas.DataFrame(candles,
                                          columns=['dateTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime',
                                                   'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol',
                                                   'takerBuyQuoteVol',
                                                   'ignore'])
        os.makedirs(target_path, exist_ok=True)
        binance_prices.to_csv(target_filename, index=False, compression="zip")

    # as timestamp is returned in ms, let us convert this back to proper timestamps.
    binance_prices['open'] = binance_prices['open'].astype(float)
    binance_prices['high'] = binance_prices['high'].astype(float)
    binance_prices['low'] = binance_prices['low'].astype(float)
    binance_prices['close'] = binance_prices['close'].astype(float)
    binance_prices['volume'] = binance_prices['volume'].astype(float)
    binance_prices.dateTime = pandas.to_datetime(binance_prices.dateTime, unit='ms')
    binance_prices.set_index('dateTime', inplace=True)
    return binance_prices


def load_prices(path: str, code: str, count_years: int) -> pandas.DataFrame:
    current_year = datetime.now().year
    df_by_period = []
    for year in range(current_year - count_years, current_year + 1):
        print(f'\nloading {year}', end=' ')
        for month in range(1, 13):
            if year == current_year and month == datetime.now().month:
                print(f'\ninterrupting at {year}/{month:02d}')
                break
            print('.', end='')
            df = load_prices_by_month(path, code, year, month)
            df = df.drop(
                ['closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'],
                axis=1)
            df_by_period.append(df)

    prices_df = pandas.concat(df_by_period, axis=0)
    prices_df.index = pandas.to_datetime(prices_df.index)
    return prices_df
