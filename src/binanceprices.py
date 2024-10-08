import io
import logging
from typing import Optional
from datetime import datetime, timedelta

import binance
import pandas

from helpers import fetch_object


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


def create_file(s3, bucket_name: str, filename: str, content: pandas.DataFrame):
    data = io.BytesIO()
    content.to_csv(data, index=False, compression="zip")
    data.seek(0)
    s3.Object(bucket_name, filename).upload_fileobj(data)
    data.close()


def load_prices_by_month(s3, bucket_name: str, code: str, year: int, month: int, force_refresh: bool = False, no_update: bool = False) -> Optional[pandas.DataFrame]:
    target_path = f'{code}/{year}'
    target_filename = f'{year}-{month:02d}.csv.zip'
    
    data_file = fetch_object(s3, bucket_name, f"{target_path}/{target_filename}", ignore_fail=True)
    if data_file is not None and not force_refresh:
        binance_prices = pandas.read_csv(data_file, compression='zip', header=0)
    elif not no_update:
        logging.info(f'no previous data found in {target_path} for month {month:02d}, loading from binance')
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
        create_file(s3, bucket_name, f"{target_path}/{target_filename}", binance_prices)

    else:
        return None

    # as timestamp is returned in ms, let us convert this back to proper timestamps.
    binance_prices['open'] = binance_prices['open'].astype(float)
    binance_prices['high'] = binance_prices['high'].astype(float)
    binance_prices['low'] = binance_prices['low'].astype(float)
    binance_prices['close'] = binance_prices['close'].astype(float)
    binance_prices['volume'] = binance_prices['volume'].astype(float)
    binance_prices.dateTime = pandas.to_datetime(binance_prices.dateTime, unit='ms')
    binance_prices.set_index('dateTime', inplace=True)
    return binance_prices


def load_prices(s3, bucket: str, code: str, count_years: int, no_update: bool = False) -> pandas.DataFrame:
    current_year = datetime.now().year
    df_by_period = []
    for year in range(current_year - count_years, current_year + 1):
        logging.info(f'loading {year}')
        for month in range(1, 13):
            if year == current_year and month == datetime.now().month:
                logging.info(f'interrupting at {year}/{month:02d}')
                break
            df = load_prices_by_month(s3, bucket, code, year, month, no_update=no_update)
            if df is not None:
                df = df.drop(
                    ['closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'],
                    axis=1)
                df_by_period.append(df)
            else:
                logging.warning(f"missing data in S3 for {code} {year}/{month}")
    
    prices_df = pandas.concat(df_by_period, axis=0)
    prices_df.index = pandas.to_datetime(prices_df.index)
    return prices_df
