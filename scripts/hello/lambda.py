import logging
import pandas

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    message = 'Hello {} {}!'.format(event['first_name'], event['last_name'])  
    return { 
        'message' : f"{message} / {pandas.DataFRame([{"id": 1, "name": "test"}])}"
    }
