import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from config import EASTERN
from models.prayerTimes import PrayerTimes, db
from observability import mosque_scope
from scraping.errors import (
    STAGE_ALL_NULL,
    STAGE_CRASH,
    STAGE_LLM,
    MosqueScrapeError,
    ScrapeJobFailed,
)
from scraping.fetch import scrape_all_mosques
from scraping.llm import call_llm
from scraping.parsing import DAILY_PRAYERS, to_prayer_fields
from scraping.prompt import build_prompt
from scraping.text import TIME_PATTERN, clean_text

logger = logging.getLogger(__name__)


@dataclass
class ScrapeRun:
    records: list[PrayerTimes]
    failures: list[MosqueScrapeError]
    total: int

    @property
    def skipped(self) -> int:
        return self.total - len(self.records) - len(self.failures)


async def process_mosque(result):
    """Return a PrayerTimes record, or None if content is unchanged. Raises MosqueScrapeError on failure."""
    name = result["name"]
    with mosque_scope(name, op="scrape.process"):
        try:
            return await build_record(result)
        except MosqueScrapeError:
            raise
        except Exception as e:
            logger.exception("Processing crashed for %s", name)
            raise MosqueScrapeError(name, STAGE_CRASH) from e


async def build_record(result):
    name = result["name"]
    cleaned_text = clean_text(result["raw_text"])

    content_hash = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()
    existing = db.session.get(PrayerTimes, name)
    if existing and existing.raw_text_hash == content_hash:
        logger.info("Skipping LLM for %s: content unchanged", name)
        return None

    today = datetime.now(EASTERN)
    prompt = build_prompt(cleaned_text, today)

    llm_response_json = await asyncio.to_thread(call_llm, prompt)
    if not llm_response_json:
        raise MosqueScrapeError(name, STAGE_LLM)

    if name == "Masjid Al-Abedeen":
        with open("prompt_abedeen.txt", "w", encoding="utf-8") as f:
            f.write(prompt)

    fields = to_prayer_fields(llm_response_json)

    daily_values = [fields[f"{p}_{slot}"] for p in DAILY_PRAYERS for slot in ("start", "iqamah")]
    if all(v is None for v in daily_values):
        logger.error(
            "LLM returned only nulls for %s, keeping existing data",
            name,
            extra={
                "input_chars": len(cleaned_text),
                "time_strings": len(TIME_PATTERN.findall(cleaned_text)),
            },
        )
        raise MosqueScrapeError(name, STAGE_ALL_NULL)

    return PrayerTimes(
        mosque_name=name,
        date=today.date(),
        **fields,
        raw_text_hash=content_hash,
        updated_at=datetime.now(timezone.utc),
    )


async def run_all() -> ScrapeRun:
    """Scrape all mosques sequentially, then run all LLM calls concurrently."""
    scraped = await scrape_all_mosques()
    pages = [r for r in scraped if not isinstance(r, MosqueScrapeError)]
    processed = await asyncio.gather(*[process_mosque(p) for p in pages], return_exceptions=True)

    outcomes = [*scraped, *processed]
    return ScrapeRun(
        records=[o for o in processed if isinstance(o, PrayerTimes)],
        failures=[o for o in outcomes if isinstance(o, MosqueScrapeError)],
        total=len(scraped),
    )


def log_summary(run: ScrapeRun):
    logger.info(
        "Scrape job finished",
        extra={
            "scrape.total": run.total,
            "scrape.updated": len(run.records),
            "scrape.skipped_unchanged": run.skipped,
            "scrape.failed": len(run.failures),
            "scrape.failed_mosques": ", ".join(str(f) for f in run.failures),
        },
    )


def scrape_and_update(app):
    with app.app_context():
        logger.info("Scrape job running")

        run = asyncio.run(run_all())

        for record in run.records:
            db.session.merge(record)
        db.session.commit()

    log_summary(run)
    if run.failures:
        raise ScrapeJobFailed(run.failures, run.total)
