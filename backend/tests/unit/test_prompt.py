from datetime import datetime
from zoneinfo import ZoneInfo
from scraping.prompt import build_prompt

EASTERN = ZoneInfo("America/Toronto")


def test_date_label_is_not_zero_padded_and_text_is_included():
    today = datetime(2026, 10, 5, 12, 0, tzinfo=EASTERN)
    cleaned = "Fajr 6:00 AM"
    prompt = build_prompt(cleaned, today)

    assert "October 5, 2026" in prompt
    assert "05" not in prompt.split("October")[1].split(",")[0]
    assert cleaned in prompt
