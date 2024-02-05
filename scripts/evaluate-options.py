import argparse
import os

import dotenv

from helpers import setup_logging_levels
from lambdas import evaluateoptions


def main():
    dotenv.load_dotenv()
    setup_logging_levels()
    parser = argparse.ArgumentParser(description='Evaluating options',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                     )
    parser.add_argument("-b", "--bucket-name", required=True, action="store", type=str, dest="bucket_name", help="AWS S3 Bucket name for storing prices")
    parser.add_argument("-i", "--instrument-code", required=True, action="store", type=str, dest="instrument_code", help="Binance instrument name (for instance ETHUSDT)")
    parser.add_argument("-c", "--cutoff-year-month", required=False, default="202201", action="store", type=str, dest="cutoff_year_month", help="Starting date for back-testing format (YYYYMM)")
    parser.add_argument("-n", "--strikes-universe-size", required=False, default=4, action="store", type=int, dest="strikes_universe_size", help="Number of options to evaluate")
    parser.add_argument("-t", "--target-period-hours", required=True, action="store", type=int, dest="target_period_hours", help="Number of hours before target expiration")
    args = parser.parse_args()
    event = {
        "binance_symbol": args.instrument_code,
        "strikes_universe_size": args.strikes_universe_size,
        "target_period_hours": args.target_period_hours,
        }
    context = {}
    os.environ["BUCKET_BINANCE_PRICES"] = args.bucket_name
    os.environ["CUT_OFF_YEAR_MONTH"] = args.cutoff_year_month
    result = evaluateoptions.handler(event, context)
    print(result)

if __name__ == "__main__":
    main()
