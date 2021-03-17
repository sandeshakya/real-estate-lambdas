import json
import os
import logging

def handler(event, context):
    logging.info(json.dumps(event))
    url = 'https://www.point2homes.com'
    search_url = url +'/CA/Real-Estate-Listings.html'
    listings = []

    # find all listings
    return dict(status=200, body=json.dumps(event))
