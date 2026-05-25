from config import settings
from ._base import run_scraper

BASE_URL = "https://www.reality.sk/byty/predaj/?lokalita={location}&cena_od={min_price}&cena_do={max_price}&plocha_od={min_area}"


def scrape() -> list[dict]:
    url = BASE_URL.format(
        location=settings.location,
        min_price=settings.min_price,
        max_price=settings.max_price,
        min_area=settings.min_area,
    )
    listings = run_scraper(url)
    for l in listings:
        l["source"] = "reality.sk"
    return listings
