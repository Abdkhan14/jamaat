import asyncio
import hashlib
from datetime import date, time
from unittest.mock import patch

import pytest

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


def test_process_mosque_raises_when_llm_fails(app_ctx, fake_llm):
    from scraping.errors import STAGE_LLM, MosqueScrapeError
    from scraping.pipeline import process_mosque
    fake_llm.return_value = None

    with pytest.raises(MosqueScrapeError) as exc_info:
        asyncio.run(process_mosque(_make_result()))
    assert exc_info.value.stage == STAGE_LLM


def test_process_mosque_rejects_all_null_daily_times(app_ctx, fake_llm, llm_response_all_null):
    from scraping.errors import STAGE_ALL_NULL, MosqueScrapeError
    from scraping.pipeline import process_mosque
    fake_llm.return_value = llm_response_all_null

    with pytest.raises(MosqueScrapeError) as exc_info:
        asyncio.run(process_mosque(_make_result()))
    assert exc_info.value.stage == STAGE_ALL_NULL


def test_process_mosque_wraps_unexpected_errors(app_ctx, fake_llm, llm_response):
    from scraping.errors import STAGE_CRASH, MosqueScrapeError
    from scraping.pipeline import process_mosque
    del llm_response["jummah1_start"]
    fake_llm.return_value = llm_response

    with pytest.raises(MosqueScrapeError) as exc_info:
        asyncio.run(process_mosque(_make_result()))
    assert exc_info.value.stage == STAGE_CRASH


def test_process_mosque_builds_record_on_success(app_ctx, fake_llm, llm_response):
    from models.prayerTimes import PrayerTimes
    from scraping.pipeline import process_mosque
    fake_llm.return_value = llm_response

    record = asyncio.run(process_mosque(_make_result()))

    assert isinstance(record, PrayerTimes)
    assert record.mosque_name == "Test Mosque"
    assert record.fajr_iqamah == time(6, 0)
    assert record.raw_text_hash == _hash(RAW_TEXT)


def test_run_all_separates_records_from_failures(app_ctx, fake_llm, llm_response):
    from scraping.errors import STAGE_FETCH, MosqueScrapeError
    from scraping.pipeline import run_all
    fake_llm.return_value = llm_response
    fetch_failure = MosqueScrapeError("Unreachable Mosque", STAGE_FETCH)

    async def fake_scrape():
        return [fetch_failure, _make_result()]

    with patch("scraping.pipeline.scrape_all_mosques", fake_scrape):
        run = asyncio.run(run_all())

    assert [r.mosque_name for r in run.records] == ["Test Mosque"]
    assert run.failures == [fetch_failure]
    assert run.skipped == 0


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


def test_scrape_and_update_commits_successes_then_fails_job(app, fake_llm, llm_response):
    from models.prayerTimes import PrayerTimes
    from scraping.errors import STAGE_FETCH, MosqueScrapeError, ScrapeJobFailed
    from scraping.pipeline import scrape_and_update
    fake_llm.return_value = llm_response

    async def fake_scrape():
        return [MosqueScrapeError("Unreachable Mosque", STAGE_FETCH), _make_result()]

    with patch("scraping.pipeline.scrape_all_mosques", fake_scrape):
        with pytest.raises(ScrapeJobFailed, match="1/2 mosques failed: Unreachable Mosque"):
            scrape_and_update(app)

    with app.app_context():
        assert [r.mosque_name for r in PrayerTimes.query.all()] == ["Test Mosque"]
