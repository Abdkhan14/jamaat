import atexit
import functools
import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from config import EASTERN
from scraping.pipeline import scrape_and_update

SCRAPE_HOUR = 3
SCRAPE_MINUTE = 0


def start_scheduler(app):
    scheduler = BackgroundScheduler(timezone=EASTERN)
    scheduler.add_job(
        func=functools.partial(scrape_and_update, app),
        trigger="cron",
        hour=SCRAPE_HOUR,
        minute=SCRAPE_MINUTE,
        id="scrape_and_update",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
        next_run_time=datetime.now(EASTERN),
    )

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())
