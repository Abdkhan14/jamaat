import json
import os
from datetime import date, time, datetime, timezone
from pathlib import Path
import pytest

# Must be set before any local import reads os.environ["OPENAI_API_KEY"].
os.environ.setdefault("OPENAI_API_KEY", "test-key")

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# App / DB
# ---------------------------------------------------------------------------

@pytest.fixture()
def app(tmp_path, monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, "start_scheduler", lambda _app: None)

    import config
    monkeypatch.setattr(config.Config, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{tmp_path}/test.db")

    flask_app = app_module.create_app()
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def app_ctx(app):
    with app.app_context():
        yield


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

@pytest.fixture()
def llm_response():
    return json.loads((FIXTURES_DIR / "llm_response.json").read_text())


@pytest.fixture()
def llm_response_all_null():
    return json.loads((FIXTURES_DIR / "llm_response_all_null.json").read_text())


@pytest.fixture()
def mosque_page_html():
    return (FIXTURES_DIR / "mosque_page.html").read_text()


# ---------------------------------------------------------------------------
# Mosque helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def known_mosque():
    from mosques import MOSQUES
    # Baitul Mukarram: has scrape_url, is not Abedeen (no prompt file side-effect)
    return dict(MOSQUES[1])


# ---------------------------------------------------------------------------
# DB row factory
# ---------------------------------------------------------------------------

@pytest.fixture()
def prayer_times_factory(app):
    from models.prayerTimes import db, PrayerTimes

    def _make(**overrides):
        defaults = dict(
            mosque_name="Test Mosque",
            date=date(2026, 10, 5),
            fajr_start=time(5, 0),
            fajr_iqamah=time(6, 0),
            zuhr_start=None,
            zuhr_iqamah=time(13, 30),
            asr_start=None,
            asr_iqamah=time(18, 0),
            maghrib_start=None,
            maghrib_iqamah=time(20, 0),
            isha_start=None,
            isha_iqamah=time(22, 0),
            jummah1_start=None,
            jummah1_iqamah=None,
            jummah2_start=None,
            jummah2_iqamah=None,
            jummah3_start=None,
            jummah3_iqamah=None,
            raw_text_hash="abc123",
            updated_at=datetime(2026, 10, 5, 3, 0, 0),
        )
        defaults.update(overrides)
        with app.app_context():
            row = PrayerTimes(**defaults)
            db.session.add(row)
            db.session.commit()
        return defaults

    return _make


# ---------------------------------------------------------------------------
# LLM mock
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_llm(monkeypatch):
    calls = []

    def _fake(prompt):
        calls.append(prompt)
        return _fake.return_value

    _fake.return_value = None
    _fake.calls = calls
    monkeypatch.setattr("scraping.pipeline.call_llm", _fake)
    return _fake


# ---------------------------------------------------------------------------
# Webhook helpers
# ---------------------------------------------------------------------------

WEBHOOK_URL = "https://example.com/webhook"


@pytest.fixture()
def webhook_env(monkeypatch):
    monkeypatch.setenv("GSHEET_WEBHOOK_URL", WEBHOOK_URL)


@pytest.fixture()
def fake_webhook_post(monkeypatch):
    posts = []

    class FakeResponse:
        def raise_for_status(self):
            pass

    def _post(url, json=None, timeout=None):
        posts.append({"url": url, "json": json})
        return FakeResponse()

    _post.posts = posts
    monkeypatch.setenv("GSHEET_WEBHOOK_URL", WEBHOOK_URL)
    monkeypatch.setattr("routes.mosque_requests.http_requests.post", _post)
    return _post
