import pandas
import binanceprices
import boto3

def handler(event, context):
    s3 = boto3.resource('s3')
    for bucket in s3.buckets.all():
        print(bucket.name)
    content = binanceprices.first_day_of_next_month(2023, 1)
    message = 'Hello {} {}!'.format(event['first_name'], event['last_name'])  
    return { 
        'message' : f"{message} / {pandas.DataFrame([{"id": 1, "name": "test"}])} / {content}"
    }
