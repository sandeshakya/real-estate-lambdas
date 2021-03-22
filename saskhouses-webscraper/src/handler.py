import logging
import os
import requests
from bs4 import BeautifulSoup


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
                "max-price": "450000",
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
                overview = page.find("div", {"class": "d-flex property-overview-data"})
                id = (
                    page.find("div", "detail-wrap")
                    .find(text="Property ID:")
                    .findNext()
                    .text
                )
                beds = (
                    overview.find("li", {"class": "h-beds"})
                    .findPrevious("li")
                    .text.strip()
                    if overview.find("li", {"class": "h-beds"}) is not None
                    else None
                )
                baths = (
                    overview.find("li", {"class": "h-baths"})
                    .findPrevious("li")
                    .text.strip()
                    if overview.find("li", {"class": "h-baths"}) is not None
                    else None
                )
                area = (
                    overview.find("li", {"class": "h-area"})
                    .findPrevious("li")
                    .text.strip()
                    if overview.find("li", {"class": "h-area"}) is not None
                    else None
                )
                year = (
                    overview.find("li", {"class": "h-year-built"})
                    .findPrevious("li")
                    .text.strip()
                    if overview.find("li", {"class": "h-year-built"}) is not None
                    else None
                )
                address = page.find("li", {"class": "detail-address"}).text

                listings.append(
                    dict(
                        id=id,
                        address=address,
                        link=link,
                        beds=beds,
                        baths=baths,
                        area=area,
                        year=year,
                        type="SASKHOUSES",
                    )
                )
    logging.info("found {} listings".format(len(listings)))
    return dict(status=200)
