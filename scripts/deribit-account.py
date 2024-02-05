import argparse
import os

import dotenv

from helpers import setup_logging_levels
from lambdas import deribitaccount, evaluateoptions


def main():
    dotenv.load_dotenv()
    setup_logging_levels()
    parser = argparse.ArgumentParser(description='Retrieving Deribit account data',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                     )
    parser.add_argument("-i", "--client-id", required=True, action="store", type=str, dest="deribit_client_id", help="Deribit Client ID")
    parser.add_argument("-s", "--client-secret", required=True, action="store", type=str, dest="deribit_client_secret", help="Deribit Client Secret")
    parser.add_argument("-c", "--currency", required=True, action="store", type=str, dest="currency", help="Deribit Currency")
    args = parser.parse_args()
    event = {
        "currency": args.currency
    }
    context = {}
    os.environ["DERIBIT_CLIENT_ID"] = args.deribit_client_id
    os.environ["DERIBIT_CLIENT_SECRET"] = args.deribit_client_secret
    result = deribitaccount.handler(event, context)
    print(result)

if __name__ == "__main__":
    main()
