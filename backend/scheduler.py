import atexit
import functools
import os
from datetime import datetime

import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from sentry_sdk.crons import monitor

from config import EASTERN
from scraping.pipeline import scrape_and_update

SCRAPE_HOUR = 3
SCRAPE_MINUTE = 0
MISFIRE_GRACE_SECONDS = 3600

SCRAPE_MONITOR_SLUG = "daily-mosque-scrape"
SCRAPE_MONITOR_CONFIG = {
    "schedule": {"type": "crontab", "value": f"{SCRAPE_MINUTE} {SCRAPE_HOUR} * * *"},
    "timezone": EASTERN.key,
    "checkin_margin": MISFIRE_GRACE_SECONDS // 60,
    "max_runtime": 15,
    "failure_issue_threshold": 1,
    "recovery_threshold": 1,
}


def run_scrape_job(app):
    # The check-in must run inside the transaction so the cron issue links to this run's trace.
    with sentry_sdk.start_transaction(op="function.cron", name="scrape_and_update"):
        with monitor(monitor_slug=SCRAPE_MONITOR_SLUG, monitor_config=SCRAPE_MONITOR_CONFIG):
            scrape_and_update(app)


def start_scheduler(app):
    scheduler = BackgroundScheduler(timezone=EASTERN)
    scheduler.add_job(
        func=functools.partial(run_scrape_job, app),
        trigger="cron",
        hour=SCRAPE_HOUR,
        minute=SCRAPE_MINUTE,
        id="scrape_and_update",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=MISFIRE_GRACE_SECONDS,
        next_run_time=datetime.now(EASTERN),
    )

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())
