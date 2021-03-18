import json
import os
import logging
import requests
from bs4 import BeautifulSoup

def handler(event, context):
    logging.info(json.dumps(event))
    url = "https://www.point2homes.com"
    search_url = url + "/CA/Real-Estate-Listings.html"
    listings = []

    page = 1
    while True:
        params = dict(
            location="Saskatoon",
            PriceMax="450000",
            Bedrooms="3plus",
            PropertyType="House",
            Bathrooms='3-4',
            YearBuiltMin='2000',
            page=page
        )
        resp=requests.get(search_url, params=params)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # get div containing all listings
        items = soup.find_all('div', {'class':'item-right=cnt'})

        for item in items:
            title = item.find('div',{'class':'address-container'}).text.strip() if item.find('div',{'class':'address-container'}) is not None else None
            link = item.find('a').get('href')
            beds = int(item.find('li',class_='ic-beds').find('strong').text)
            baths = int(item.find('li',{'class':'ic-baths'}).find('strong').text) if item.find('li',{'class':'ic-baths'}) is not None else None
            sqft = (lambda x: int(x.replace(',','')))(item.find('li',{'class':'ic-sqft'}).find('strong').text)
            price = (lambda x: int(x.replace('$', '').replace('CAD','').replace(',','')))(item.find('div',{'class':'price'}).text.strip())
            lat = int(item.find('input',id=lambda x:x.startswith('Latitude')).get('value'))
            long = int(item.find('input',id=lambda x:x.startswith('Longitude')).get('value'))
            listings.append(dict(
                title = title,
                link = link,
                beds = beds,
                baths = baths,
                sqft = sqft,
                price = price,
                lat = lat,
                long = long,
            ))
            if soup.find('li',class_='next')== None:
                break
            else:
                page += 1
    print(listings)
    # find all listings
    return dict(status=200, body=json.dumps(event))
