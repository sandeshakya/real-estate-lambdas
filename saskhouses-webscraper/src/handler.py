import logging
import os
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Attr
import time

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME"))
logging.getLogger().setLevel(logging.INFO)

def insertToTable(item: dict) -> int:
    """
    Inserts item dynamodb Table
    """
    try:
        table.put_item(
            Item={
                "id": item["id"],
                "type": "SASKHOUSES",
                "createdat": Decimal(str(round(time.time() * 1000))),
                "address": item["address"],
                "link": item["link"],
                "beds": item["beds"],
                "baths": Decimal(str(item["baths"])),
                "area": item["area"],
                "price": item["price"],
            },
            ConditionExpression=Attr("id").not_exists(),
        )
        return 1
    except Exception as e:
        return 0


def handler(event, context):
    base_url = "https://saskhouses.com"
    search_url = base_url + "/search-results-2"
    header = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    BED_MIN = event["bedsMin"]
    BED_MAX = event["bedsMax"]
    listings = []

    logging.info("Searching for houses...")
    for bed in range(BED_MIN, BED_MAX + 1):
        for bath in range(3, bed + 1):
            params = {
                "location[]": "saskatoon",
                "type[]": "residential",
                "status[]": "for-sale",
                "bedrooms": str(bed),
                "bathrooms": str(bath),
                "min-price":event['minPrice'],
                "max-price": event['maxPrice'],
            }

            resp = requests.get(url=search_url, params=params, headers=header)
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.find_all(
                "div", {"class": "item-listing-wrap hz-item-gallery-js card"}
            )
            if len(items) == 0:
                continue
            for item in items:
                link = item.find("a", {"class": "btn"}).get("href")
                page = BeautifulSoup(
                    requests.get(url=link, headers=header).text, "html.parser"
                )
                address = page.find("li", {"class": "detail-address"}).text
                details = page.find("div", "detail-wrap")
                id = (
                    details.find(text="Property ID:").findNext().text.strip()
                    if details.find(text="Property ID:") is not None
                    else None
                )
                price = (
                    details.find(text="Price:").findNext().text.strip()
                    if details.find(text="Price:") is not None
                    else None
                )
                area = (
                    details.find(text="Property Size:").findNext().text.strip()
                    if details.find(text="Property Size:") is not None
                    else None
                )
                beds = (
                    details.find(text="Bedrooms:").findNext().text.strip()
                    if details.find(text="Bedrooms:") is not None
                    else None
                )
                baths = (
                    details.find(text="Bathrooms:").findNext().text.strip()
                    if details.find(text="Bathrooms:") is not None
                    else None
                )
                year = (
                    details.find(text="Year Built:").findNext().text.strip()
                    if details.find(text="Year Built:") is not None
                    else None
                )

                listings.append(
                    dict(
                        id=id,
                        address=address,
                        link=link,
                        beds=beds,
                        baths=baths,
                        area=[int(i) for i in area.split() if i.isdigit()][0]
                        if area is not None
                        else None,
                        price=(
                            lambda x: int(
                                x.replace("$", "").replace("CAD", "").replace(",", "")
                            )
                        )(price),
                        year=year,
                    )
                )
    logging.info("found {} listings".format(len(listings)))
    logging.info("adding listings to table...")
    logging.info(
        "{} listings added to table".format(
            sum([insertToTable(listing) for listing in listings])
        )
    )
    return dict(status=200)
