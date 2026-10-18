from unittest.mock import MagicMock, patch
import requests as _requests

LONG_NAME = "A" * 201
LONG_INFO = "B" * 2001


def test_returns_503_without_webhook_env(client, monkeypatch):
    monkeypatch.delenv("GSHEET_WEBHOOK_URL", raising=False)
    resp = client.post("/mosque-request", json={"mosque_name": "Test"})
    assert resp.status_code == 503


def test_returns_400_when_name_missing(client):
    resp = client.post("/mosque-request", json={})
    assert resp.status_code == 400


def test_returns_400_when_field_too_long(client, webhook_env):
    resp = client.post("/mosque-request", json={"mosque_name": LONG_NAME})
    assert resp.status_code == 400

    resp = client.post("/mosque-request", json={"mosque_name": "Test", "additional_info": LONG_INFO})
    assert resp.status_code == 400


def test_returns_201_and_forwards_payload_with_submitter_ip(client, fake_webhook_post):
    resp = client.post(
        "/mosque-request",
        json={"mosque_name": "Test Mosque", "additional_info": "Some details"},
        headers={"X-Forwarded-For": "1.2.3.4"},
    )
    assert resp.status_code == 201
    assert len(fake_webhook_post.posts) == 1
    payload = fake_webhook_post.posts[0]["json"]
    assert payload["mosque_name"] == "Test Mosque"
    assert payload["additional_info"] == "Some details"
    assert payload["submitter_ip"] == "1.2.3.4"


def test_returns_502_when_webhook_fails(client, monkeypatch):
    monkeypatch.setenv("GSHEET_WEBHOOK_URL", "https://example.com/webhook")

    def _failing_post(*args, **kwargs):
        raise _requests.exceptions.ConnectionError("down")

    monkeypatch.setattr("routes.mosque_requests.http_requests.post", _failing_post)
    resp = client.post("/mosque-request", json={"mosque_name": "Test"})
    assert resp.status_code == 502
