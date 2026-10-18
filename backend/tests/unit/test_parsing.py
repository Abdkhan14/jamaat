from datetime import time
from scraping.parsing import format_time, normalize_prayer_times


def test_format_time_parses_ampm():
    assert format_time("6:30 PM") == time(18, 30)
    assert format_time("5:00 AM") == time(5, 0)


def test_format_time_returns_none_for_nullish_and_invalid():
    for value in [None, "null", "none", "NONE", "sunset", "12:00"]:
        assert format_time(value) is None


def test_normalize_swaps_reversed_pair():
    prayer = {
        "fajr_start": "6:00 AM",
        "fajr_iqamah": "5:00 AM",  # reversed
        "zuhr_start": None, "zuhr_iqamah": None,
        "asr_start": None, "asr_iqamah": None,
        "maghrib_start": None, "maghrib_iqamah": None,
        "isha_start": None, "isha_iqamah": None,
    }
    result = normalize_prayer_times(prayer)
    assert result["fajr_start"] == "5:00 AM"
    assert result["fajr_iqamah"] == "6:00 AM"


def test_normalize_moves_lone_start_to_iqamah():
    prayer = {
        "fajr_start": "6:00 AM",
        "fajr_iqamah": None,
        "zuhr_start": None, "zuhr_iqamah": None,
        "asr_start": None, "asr_iqamah": None,
        "maghrib_start": None, "maghrib_iqamah": None,
        "isha_start": None, "isha_iqamah": None,
    }
    result = normalize_prayer_times(prayer)
    assert result["fajr_start"] is None
    assert result["fajr_iqamah"] == "6:00 AM"
