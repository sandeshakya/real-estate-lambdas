import os
import json
import logging
from requests import get, Request
import boto3
from boto3.dynamodb.conditions import Attr
import time
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME"))
logging.getLogger().setLevel(logging.INFO)

base_url = 'https://www.remax.ca'


def to_matrix(l, n):
    """
    convert list `l` to matrix of `n` elements
    """
    return [l[i:i+n] for i in range(0, len(l), n)]


def insertToTable(item):
    """
    Inserts item dynamodb Table
    """
    try:
        table.put_item(
            Item={
                "id": item['id'],
                "type": 'REMAX',
                'createdat': Decimal(str(round(time.time()*1000))),
                "address": item['address'],
                "link": base_url + '/' + item['link'],
                "beds": item['beds'],
                "baths": item['baths'],
                "area": Decimal(item['area']),
                "price": item['price'],
                "lat": Decimal(str(item['lat'])),
                "long": Decimal(str(item['long'])),

            },
            ConditionExpression=Attr("id").not_exists(),
        )
        return 1
    except Exception as e:
        print(e)
        return 0


def handler(event, context):
    api_base_url = 'https://api.remax.ca/api/v1/listings/active'
    preview_base_url = base_url + '/api/v1/listings/previews'
    params = {
        'north': 52.28424538687483,
        'east': -105.4183754130878,
        'south': 52.03149632105883,
        'west': -107.92193998691221,
        'features.listingTypeIds': 100,
        'features.PriceListMin': event['minPrice'],
        'features.PriceListMax': event['maxPrice'],
        'features.BedsMin': event['minBeds'],
        'features.BathsMin': event['menBaths'],
        'isPhysicalLocationSearch': True,
        'includeSortFields': True
    }
    # need this param because another param with same key already exists
    extra_param = '&features.listingTypeIds=155'

    # first get all the eligible listing ids
    req = Request('GET', api_base_url,
                  params=params).prepare().url + extra_param

    resp = get(url=req)
    ids = [i.split(';')[2] for i in json.loads(resp.text)['result']['results']]
    print(len(ids))
    # get listings by chunks of 20
    listing_chunks = to_matrix(ids, 20)

    # get listings for each chunk
    previews = []
    for chunk in listing_chunks:
        url = '{}/{}?includeOffice=true'.format(
            preview_base_url, ','.join(chunk))
        results = json.loads(get(url=url).text)['result']['results']
        for result in results:
            previews.append(result)
    listings = []
    for preview in previews:
        try:
            listings.append(
                dict(
                    id=preview['listingId'],
                    address=','.join(
                        [preview['address'], preview['city'], preview['province'], preview['postalCode']]),
                    link=preview['detailUrl'],
                    beds=preview['beds'],
                    baths=preview['baths'],
                    area=preview['sqFtSearch'],
                    price=preview['listPrice'],
                    lat=preview['lat'],
                    long=preview['lng']
                )
            )
        except Exception as e:
            continue

    logging.info("found {} listings".format(len(listings)))
    logging.info("adding listings to table...")
    logging.info(
        "{} listings added to table".format(
            sum([insertToTable(listing) for listing in listings])
        )
    )

    return dict(status=200)
