import argparse
from helpers import setup_logging_levels
from lambdas import aggregateprices


def main():
    setup_logging_levels()
    parser = argparse.ArgumentParser(description='Matching stock codes from various systems',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                     )
    parser.add_argument("-b", "--bucket-name", required=True, action="store", type=str, dest="bucket_name", help="AWS S3 Bucket name for storing prices")
    parser.add_argument("-i", "--instrument-code", required=True, action="store", type=str, dest="instrument_code", help="Binance instrument name (for instance ETHUSDT)")
    parser.add_argument("-n", "--count-years", required=True, action="store", type=int, dest="count_years", help="Number of years to look for")
    event = parser.parse_args()
    context = {}
    result = aggregateprices.handler(event.__dict__, context)
    print(result)

if __name__ == "__main__":
    main()
