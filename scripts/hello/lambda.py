import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    message = 'Hello {} {}!'.format(event['first_name'], event['last_name'])  
    return { 
        'message' : message
    }
