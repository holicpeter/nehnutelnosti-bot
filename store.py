import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

SEEN_FILE = Path("seen_listings.json")
LISTINGS_FILE = Path("listings_data.json")
MAX_STORED = 500


def _load_seen() -> set[str]:
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()


def _save_seen(seen: set[str]) -> None:
    SEEN_FILE.write_text(json.dumps(list(seen)))


def _load_listings() -> list[dict]:
    if LISTINGS_FILE.exists():
        return json.loads(LISTINGS_FILE.read_text())
    return []


def _save_listings(listings: list[dict]) -> None:
    LISTINGS_FILE.write_text(json.dumps(listings[-MAX_STORED:], ensure_ascii=False))


def listing_id(listing: dict) -> str:
    key = (listing.get("url") or listing.get("title", "")).strip()
    return hashlib.sha1(key.encode()).hexdigest()


def filter_new(listings: list[dict]) -> list[dict]:
    seen = _load_seen()
    new = [l for l in listings if listing_id(l) not in seen]
    if new:
        now = datetime.now(timezone.utc).isoformat()
        for l in new:
            l["seen_at"] = now
        seen.update(listing_id(l) for l in new)
        _save_seen(seen)
        stored = _load_listings()
        stored.extend(new)
        _save_listings(stored)
    return new


def get_all_listings() -> list[dict]:
    listings = _load_listings()
    return list(reversed(listings))


def get_stats() -> dict:
    listings = _load_listings()
    seen = _load_seen()
    sources: dict[str, int] = {}
    for l in listings:
        src = l.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
    return {
        "total": len(seen),
        "stored": len(listings),
        "by_source": sources,
    }
