from decimal import Decimal
import json
import os
import logging
import requests
from bs4 import BeautifulSoup
import boto3
from boto3.dynamodb.conditions import Attr
from mypy_boto3_dynamodb import DynamoDBServiceResource

dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME"))


def insertToTable(item: dict) -> int:
    """
    Inserts item dynamodb Table
    """
    try:
        table.put_item(
            Item={
                "id": item['id'],
                "title": item['title'],
                "link": item['link'],
                "beds": item['beds'],
                "baths": Decimal(str(item['baths'])),
                "sqft": item['sqft'],
                "price": item['price'],
                "lat": Decimal(str(item['lat'])),
                "long": Decimal(str(item['long'])),
            },
            ConditionExpression=Attr("id").not_exists(),
        )
        return 1
    except Exception as e:
        return 0


def handler(event, context):
    url = "https://www.point2homes.com"
    search_url = url + "/CA/Real-Estate-Listings.html"
    listings = []

    page = 1
    while True:
        params = {**event,'page':page}
        header = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        resp = requests.get(search_url, params=params, headers=header)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.find_all("div", {"class": "item-right-cnt"})

        for item in items:
            title = (
                item.find("div", {"class": "address-container"}).text.strip()
                if item.find("div", {"class": "address-container"}) is not None
                else None
            )
            link = item.find("a").get("href")
            id = link.split("/")[-1].split(".")[0]
            beds = int(item.find("li", class_="ic-beds").find("strong").text)
            baths = (
                float(item.find("li", {"class": "ic-baths"}).find("strong").text)
                if item.find("li", {"class": "ic-baths"}) is not None
                else None
            )
            sqft = (lambda x: int(x.replace(",", "")))(
                item.find("li", {"class": "ic-sqft"}).find("strong").text
            )
            price = (
                lambda x: int(x.replace("$", "").replace("CAD", "").replace(",", ""))
            )(item.find("div", {"class": "price"}).text.strip())
            lat = float(
                item.find("input", id=lambda x: x.startswith("Latitude")).get("value")
            )
            long = float(
                item.find("input", id=lambda x: x.startswith("Longitude")).get("value")
            )
            listings.append(
                dict(
                    id=id,
                    title=title,
                    link=link,
                    beds=beds,
                    baths=baths,
                    sqft=sqft,
                    price=price,
                    lat=lat,
                    long=long,
                )
            )
        if soup.find("li", class_="next") == None:
            break
        else:
            page += 1
    logging.info("found {} listings".format(len(listings)))
    logging.info("adding listings to table...")
    logging.info(
        "{} listings added to table".format(
            sum([insertToTable(listing) for listing in listings])
        )
    )
    return dict(status=200)
