from config import settings
from ._base import run_scraper

BASE_URL = "https://www.nehnutelnosti.sk/predaj/byty/{location}/?price_to={max_price}&price_from={min_price}&area_from={min_area}"


def scrape() -> list[dict]:
    url = BASE_URL.format(
        location=settings.location.lower(),
        min_price=settings.min_price,
        max_price=settings.max_price,
        min_area=settings.min_area,
    )
    listings = run_scraper(url)
    for l in listings:
        l["source"] = "nehnutelnosti.sk"
    return listings
