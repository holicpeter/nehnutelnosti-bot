from config import settings
from ._base import run_scraper

BASE_URL = "https://www.topreality.sk/vyhladavanie-nehnutelnosti.html?type=1&transaction=1&location={location}&priceFrom={min_price}&priceTo={max_price}&areaFrom={min_area}"


def scrape() -> list[dict]:
    url = BASE_URL.format(
        location=settings.location,
        min_price=settings.min_price,
        max_price=settings.max_price,
        min_area=settings.min_area,
    )
    listings = run_scraper(url)
    for l in listings:
        l["source"] = "topreality.sk"
    return listings
