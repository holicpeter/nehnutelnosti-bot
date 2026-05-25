from scrapegraphai.graphs import SmartScraperGraph
from config import settings

GRAPH_CONFIG = {
    "llm": {
        "api_key": settings.openai_api_key,
        "model": "openai/gpt-4o-mini",
    },
    "verbose": False,
    "headless": True,
}

LISTING_SCHEMA = """
Return a JSON array of real-estate listings found on the page.
Each item must have these fields (use null if not available):
  - title: string
  - price: number (EUR, without currency symbol)
  - area: number (m², without unit)
  - location: string
  - url: string (absolute URL of the listing detail page)
  - image_url: string
  - description: string (short summary, max 300 chars)
Return only the JSON array, no extra text.
"""


def run_scraper(url: str, prompt: str | None = None) -> list[dict]:
    prompt = prompt or LISTING_SCHEMA
    graph = SmartScraperGraph(
        prompt=prompt,
        source=url,
        config=GRAPH_CONFIG,
    )
    result = graph.run()
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        for v in result.values():
            if isinstance(v, list):
                return v
    return []
