from config import settings
from ._base import run_scraper

BASE_URL = "https://reality.bazos.sk/byt/?hledat=&rubriky=byt&hlokalita={location}&cena={max_price}&Submit=Hledat"


def scrape() -> list[dict]:
    url = BASE_URL.format(
        location=settings.location,
        max_price=settings.max_price,
    )
    listings = run_scraper(url)
    for l in listings:
        l["source"] = "bazos.sk"
    return listings
