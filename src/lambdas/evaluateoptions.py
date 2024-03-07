import boto3
import logging
import os

import pandas

import optionspricing
import helpers

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    target_period_hours = event["target_period_hours"]
    strikes_universe_size = event["strikes_universe_size"]
    binance_symbol = event["binance_symbol"]
    cut_off_year_month = int(os.environ["CUT_OFF_YEAR_MONTH"][:4]), int(os.environ["CUT_OFF_YEAR_MONTH"][4:6])
    bucket_name = os.environ["BUCKET_BINANCE_PRICES"]

    instrument_code = binance_symbol[:3]

    headers = {"Content-Type": "application/json"}
    base_url = "https://www.deribit.com/api/v2/public"

    trading_model = optionspricing.TradingModel(base_url, headers, instrument_code, target_period_hours)
    trading_model.cutoff_year_month(cut_off_year_month)

    s3 = boto3.resource('s3')

    data_file = helpers.fetch_object(s3, bucket_name, f"{binance_symbol}-full.csv.zip")

    prices_df = pandas.read_csv(data_file, compression='zip', header=0, index_col="dateTime")
    prices_df.index = pandas.to_datetime(prices_df.index)
    option_chain_df = trading_model.evaluate(prices_df, strikes_universe_size)
    simulation = trading_model.simulate_strategy_long_straddle(option_chain_df, strikes_universe_size)
    #allocation = simulation.allocate([1, 2], 1500. * 2./100.)

    message = f"""{simulation}"""
    helpers.notify_slack(message)
    return { 
        'message' : message
    }
