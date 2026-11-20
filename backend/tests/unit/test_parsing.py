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


# ---------------------------------------------------------------------------
# Jummah slot sort
# ---------------------------------------------------------------------------

def _base_daily():
    """Return a dict with all daily prayer fields set to None."""
    return {
        "fajr_start": None, "fajr_iqamah": None,
        "zuhr_start": None, "zuhr_iqamah": None,
        "asr_start": None, "asr_iqamah": None,
        "maghrib_start": None, "maghrib_iqamah": None,
        "isha_start": None, "isha_iqamah": None,
    }


def test_jummah_sort_reorders_out_of_order_slots():
    """LLM returned jummah3 as the earliest — sort must fix it."""
    prayer = {
        **_base_daily(),
        "jummah1_start": None, "jummah1_iqamah": "1:45 PM",
        "jummah2_start": None, "jummah2_iqamah": "2:30 PM",
        "jummah3_start": None, "jummah3_iqamah": "1:00 PM",  # out of order
    }
    result = normalize_prayer_times(prayer)
    assert result["jummah1_iqamah"] == "1:00 PM"
    assert result["jummah2_iqamah"] == "1:45 PM"
    assert result["jummah3_iqamah"] == "2:30 PM"


def test_jummah_sort_keeps_start_and_iqamah_together():
    """When a slot has both start and iqamah, moving the slot keeps the pair."""
    prayer = {
        **_base_daily(),
        # Slot 1 has only iqamah at 2:00 PM
        "jummah1_start": None, "jummah1_iqamah": "2:00 PM",
        # Slot 2 has a full pair with iqamah at 1:00 PM (earlier — should become slot 1)
        "jummah2_start": "12:30 PM", "jummah2_iqamah": "1:00 PM",
        "jummah3_start": None, "jummah3_iqamah": None,
    }
    result = normalize_prayer_times(prayer)
    assert result["jummah1_start"] == "12:30 PM"
    assert result["jummah1_iqamah"] == "1:00 PM"
    assert result["jummah2_start"] is None
    assert result["jummah2_iqamah"] == "2:00 PM"
    assert result["jummah3_start"] is None
    assert result["jummah3_iqamah"] is None


def test_jummah_sort_moves_empty_slots_last():
    """Slots with no time should sink to the end."""
    prayer = {
        **_base_daily(),
        "jummah1_start": None, "jummah1_iqamah": None,
        "jummah2_start": None, "jummah2_iqamah": "1:30 PM",
        "jummah3_start": None, "jummah3_iqamah": None,
    }
    result = normalize_prayer_times(prayer)
    assert result["jummah1_iqamah"] == "1:30 PM"
    assert result["jummah2_iqamah"] is None
    assert result["jummah3_iqamah"] is None


def test_jummah_sort_tolerates_missing_jummah_keys():
    """LLM omitted all jummah keys — should not raise KeyError."""
    prayer = {**_base_daily()}
    result = normalize_prayer_times(prayer)
    for n in (1, 2, 3):
        assert result[f"jummah{n}_start"] is None
        assert result[f"jummah{n}_iqamah"] is None


def test_jummah_sort_already_ordered_is_unchanged():
    """Correctly ordered slots should remain unchanged."""
    prayer = {
        **_base_daily(),
        "jummah1_start": None, "jummah1_iqamah": "1:00 PM",
        "jummah2_start": None, "jummah2_iqamah": "1:45 PM",
        "jummah3_start": None, "jummah3_iqamah": "2:30 PM",
    }
    result = normalize_prayer_times(prayer)
    assert result["jummah1_iqamah"] == "1:00 PM"
    assert result["jummah2_iqamah"] == "1:45 PM"
    assert result["jummah3_iqamah"] == "2:30 PM"
