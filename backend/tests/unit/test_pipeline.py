import asyncio
import hashlib
from datetime import date, time
from unittest.mock import patch

from scraping.text import clean_text


def _hash(text):
    return hashlib.sha256(clean_text(text).encode()).hexdigest()


RAW_TEXT = "Fajr 5:00 AM 6:00 AM  Zuhr 1:00 PM 1:30 PM  Asr 5:00 PM 6:00 PM  Maghrib 8:00 PM  Isha 9:30 PM 10:00 PM"


def _make_result(mosque_name="Test Mosque", raw_text=RAW_TEXT):
    return {"name": mosque_name, "raw_text": raw_text}


def test_process_mosque_skips_llm_when_hash_unchanged(app_ctx, prayer_times_factory, fake_llm):
    from scraping.pipeline import process_mosque
    prayer_times_factory(mosque_name="Test Mosque", raw_text_hash=_hash(RAW_TEXT))

    result = asyncio.run(process_mosque(_make_result()))

    assert result is None
    assert len(fake_llm.calls) == 0


def test_process_mosque_returns_none_when_llm_fails(app_ctx, fake_llm, llm_response):
    from scraping.pipeline import process_mosque
    fake_llm.return_value = None

    result = asyncio.run(process_mosque(_make_result()))
    assert result is None


def test_process_mosque_rejects_all_null_daily_times(app_ctx, fake_llm, llm_response_all_null):
    from scraping.pipeline import process_mosque
    fake_llm.return_value = llm_response_all_null

    result = asyncio.run(process_mosque(_make_result()))
    assert result is None


def test_process_mosque_builds_record_on_success(app_ctx, fake_llm, llm_response):
    from models.prayerTimes import PrayerTimes
    from scraping.pipeline import process_mosque
    fake_llm.return_value = llm_response

    record = asyncio.run(process_mosque(_make_result()))

    assert isinstance(record, PrayerTimes)
    assert record.mosque_name == "Test Mosque"
    assert record.fajr_iqamah == time(6, 0)
    assert record.raw_text_hash == _hash(RAW_TEXT)


def test_run_all_drops_failed_scrapes_and_rejections(app_ctx, fake_llm, llm_response):
    from scraping.pipeline import run_all
    fake_llm.return_value = llm_response

    with patch("scraping.pipeline.scrape_all_mosques", return_value=[
        asyncio.coroutine(lambda: [None, _make_result()])()
        if False else None
    ]):
        pass

    # Patch scrape_all_mosques to return one failed (None) and one valid result
    async def fake_scrape():
        return [None, _make_result()]

    with patch("scraping.pipeline.scrape_all_mosques", fake_scrape):
        records = asyncio.run(run_all())

    assert len(records) == 1


def test_scrape_and_update_merges_and_commits(app, prayer_times_factory, fake_llm, llm_response):
    from models.prayerTimes import db, PrayerTimes
    from scraping.pipeline import scrape_and_update

    prayer_times_factory(mosque_name="Test Mosque")
    fake_llm.return_value = llm_response

    async def fake_scrape():
        return [_make_result()]

    with patch("scraping.pipeline.scrape_all_mosques", fake_scrape):
        scrape_and_update(app)

    with app.app_context():
        rows = PrayerTimes.query.all()

    assert len(rows) == 1
    assert rows[0].mosque_name == "Test Mosque"
