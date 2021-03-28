import boto3
from boto3.dynamodb.conditions import Key
import os
import json
from datetime import datetime, timedelta
import logging

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME"))
logging.getLogger().setLevel(logging.INFO)

sns = boto3.resource('sns')
topic = sns.Topic(os.environ.get('SNS_TOPIC'))
listing_types = ['POINT2HOMES', 'SASKHOUSES']
point2home_baseurl = 'https://www.point2homes.com'


def handler(event, context):
    links = []
    for listing_type in listing_types:

        resp = table.query(
            IndexName='type-createdat-index',
            KeyConditionExpression=Key('type').eq(listing_type) & Key('createdat').gte(
                round(datetime.timestamp(datetime.now() - timedelta(minutes=5))*1000))

        )
        for item in resp['Items']:
            links.append(item['link'] if listing_type ==
                         'SASKHOUSES' else point2home_baseurl + item['link'])
    logging.info('Found {} new listings'.format(len(links)))

    if len(links) > 0:
        topic.publish(
            MessageStructure='json',
            Subject='Found new Listings',
            Message=json.dumps({
                'default': 'Found {} new listings. Check your email'.format(len(links)),
                'email': "Found these {} new listings!\n\n{}".format(len(links), '\n\n'.join(links))
            })
        )
        logging.info('Messages sent')
    return {'status': 200}
