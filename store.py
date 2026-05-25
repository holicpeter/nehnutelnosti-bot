import json
import hashlib
from pathlib import Path

STORE_FILE = Path("seen_listings.json")


def _load() -> set[str]:
    if STORE_FILE.exists():
        return set(json.loads(STORE_FILE.read_text()))
    return set()


def _save(seen: set[str]) -> None:
    STORE_FILE.write_text(json.dumps(list(seen)))


def listing_id(listing: dict) -> str:
    key = (listing.get("url") or listing.get("title", "")).strip()
    return hashlib.sha1(key.encode()).hexdigest()


def filter_new(listings: list[dict]) -> list[dict]:
    seen = _load()
    new = [l for l in listings if listing_id(l) not in seen]
    seen.update(listing_id(l) for l in new)
    _save(seen)
    return new
