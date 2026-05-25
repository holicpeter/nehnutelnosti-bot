import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from store import filter_new, get_all_listings, get_stats
from notifier.email import notify
import scrapers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

ON_VERCEL = bool(os.environ.get("VERCEL"))

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not ON_VERCEL:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            run_scraping_job,
            "interval",
            hours=settings.scrape_interval_hours,
            id="scraping_job",
        )
        scheduler.start()
        log.info("Scheduler spustený (každých %dh)", settings.scrape_interval_hours)
        app.state.scheduler = scheduler
    yield
    if not ON_VERCEL and hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()


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


@app.get("/api/cron/scrape")
def cron_scrape(request: Request):
    """Vercel Cron Job endpoint — called automatically every hour."""
    auth = request.headers.get("authorization", "")
    if settings.cron_secret and auth != f"Bearer {settings.cron_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    run_scraping_job()
    return {"status": "done"}


@app.get("/health")
def health():
    scheduler = getattr(app.state, "scheduler", None)
    job = scheduler.get_job("scraping_job") if scheduler else None
    return {
        "status": "ok",
        "mode": "vercel" if ON_VERCEL else "local",
        "next_run": str(job.next_run_time) if job else "managed by Vercel Cron",
        "interval_hours": settings.scrape_interval_hours,
    }
