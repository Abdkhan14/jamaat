import json
from unittest.mock import MagicMock, patch
from scraping.llm import call_llm

VALID_JSON = {"fajr_iqamah": "6:00 AM"}


def _make_completion(content):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


def test_call_llm_returns_parsed_json():
    with patch("scraping.llm.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_completion(json.dumps(VALID_JSON))
        result = call_llm("test prompt")
    assert result == VALID_JSON


def test_call_llm_returns_none_on_failure():
    with patch("scraping.llm.client") as mock_client:
        mock_client.chat.completions.create.side_effect = RuntimeError("API down")
        assert call_llm("test prompt") is None

    with patch("scraping.llm.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_completion("not json {{{")
        assert call_llm("test prompt") is None
