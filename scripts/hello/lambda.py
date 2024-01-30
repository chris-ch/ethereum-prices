import logging

from binanceprices import first_day_of_next_month

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    message = 'Hello {} {}!'.format(event['first_name'], event['last_name'])  
    return { 
        'message' : f"{message} / {first_day_of_next_month(2023, 1)}"
    }
