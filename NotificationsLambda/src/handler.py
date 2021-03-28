import boto3
from boto3.dynamodb.conditions import Key
import os
from datetime import datetime, timedelta

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME"))

def handler(event,context):
    resp = table.query(
        Select='ALL_ATTRIBUTES',
        KeyConditionExpression=Key('timestamp').gte(round(datetime.timestamp(datetime.now() - timedelta(hours=1))*1000))
    )
    print(resp)

    return {'status':200}