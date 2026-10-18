from unittest.mock import patch
import respx
import httpx
from scraping.fetch import fetch_via_requests


def test_strips_script_style_noscript(mosque_page_html, known_mosque):
    with respx.mock:
        url = known_mosque["scrape_url"]
        respx.get(url).mock(return_value=httpx.Response(200, text=mosque_page_html))
        result = fetch_via_requests(known_mosque)

    assert result is not None
    assert "should not appear" not in result["raw_text"]
    assert "Enable JavaScript" not in result["raw_text"]
    assert "color: red" not in result["raw_text"]
    assert "Fajr" in result["raw_text"]


def test_uses_scrape_url_over_website(known_mosque):
    scrape_url = known_mosque["scrape_url"]
    with respx.mock:
        respx.get(scrape_url).mock(return_value=httpx.Response(200, text="<p>times</p>"))
        result = fetch_via_requests(known_mosque)
    assert result is not None


def test_retries_then_returns_none(known_mosque):
    with respx.mock, patch("scraping.fetch.time.sleep") as mock_sleep:
        respx.get(known_mosque["scrape_url"]).mock(side_effect=httpx.ConnectError("timeout"))
        result = fetch_via_requests(known_mosque, retries=3)

    assert result is None
    assert mock_sleep.call_count == 2  # sleeps between attempts 1→2 and 2→3
