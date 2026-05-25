import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler

from config import settings
from store import filter_new, get_all_listings, get_stats
from notifier.email import notify
import scrapers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SCRAPER_FNS = [
    scrapers.scrape_reality_sk,
    scrapers.scrape_nehnutelnosti_sk,
    scrapers.scrape_topreality_sk,
    scrapers.scrape_bazos_sk,
]

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def run_scraping_job() -> None:
    log.info("Spúšťam scraping job...")
    all_listings: list[dict] = []
    for fn in SCRAPER_FNS:
        try:
            results = fn()
            log.info("%s: %d inzerátov", fn.__module__, len(results))
            all_listings.extend(results)
        except Exception as e:
            log.error("Chyba v %s: %s", fn.__module__, e)

    new = filter_new(all_listings)
    log.info("Nových inzerátov: %d", len(new))

    if new:
        try:
            notify(new)
            log.info("Email odoslaný (%d inzerátov)", len(new))
        except Exception as e:
            log.error("Chyba pri odosielaní emailu: %s", e)


scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        run_scraping_job,
        "interval",
        hours=settings.scrape_interval_hours,
        id="scraping_job",
    )
    scheduler.start()
    log.info("Scheduler spustený (každých %dh)", settings.scrape_interval_hours)
    yield
    scheduler.shutdown()


app = FastAPI(title="Nehnuteľnosti Bot", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/listings")
def api_listings():
    return get_all_listings()


@app.get("/api/stats")
def api_stats():
    return get_stats()


@app.post("/scrape/now")
def scrape_now():
    run_scraping_job()
    return {"status": "done"}


@app.get("/health")
def health():
    job = scheduler.get_job("scraping_job")
    return {
        "status": "ok",
        "next_run": str(job.next_run_time) if job else None,
        "interval_hours": settings.scrape_interval_hours,
    }
