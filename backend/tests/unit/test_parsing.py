from pathlib import Path
from datetime import time
from scraping.parsing import format_time, normalize_prayer_times, extract_trailing_jummah, to_prayer_fields
from scraping.text import clean_text

CASES_DIR = Path(__file__).parent.parent.parent / "evals" / "cases"


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


# ---------------------------------------------------------------------------
# extract_trailing_jummah + to_prayer_fields(cleaned_text=...) override
# ---------------------------------------------------------------------------

# The exact bad output the production LLM generated on Nov 23 for Baitul Aman.
_AMAN_BAD_LLM_JSON = {
    "fajr_start": None, "fajr_iqamah": "6:30 AM",
    "zuhr_start": "12:04 PM", "zuhr_iqamah": "1:00 PM",
    "asr_start": "2:26 PM", "asr_iqamah": "3:30 PM",
    "maghrib_start": "4:45 PM", "maghrib_iqamah": "4:50 PM",
    "isha_start": "6:09 PM", "isha_iqamah": "7:00 PM",
    # LLM mis-paired: treated 12:30 PM as a start, 1:25 PM as iqamah, dropped 2:10 PM
    "jummah1_start": "12:30 PM", "jummah1_iqamah": "1:25 PM",
    "jummah2_start": None,       "jummah2_iqamah": "2:10 PM",
    "jummah3_start": None,       "jummah3_iqamah": None,
}


def test_extract_trailing_jummah_matches_aman():
    """Parser finds all three Aman slots and returns None starts."""
    text = clean_text((CASES_DIR / "trailing_jummah_first_slot.txt").read_text())
    result = extract_trailing_jummah(text)
    assert result is not None
    assert result["jummah1_start"] is None
    assert result["jummah1_iqamah"] == "12:30 PM"
    assert result["jummah2_start"] is None
    assert result["jummah2_iqamah"] == "1:25 PM"
    assert result["jummah3_start"] is None
    assert result["jummah3_iqamah"] == "2:10 PM"


def test_extract_trailing_jummah_matches_mukarram():
    """Parser works on the Baitul Mukarram snapshot too."""
    text = clean_text((CASES_DIR / "jummah_matches_zuhr.txt").read_text())
    result = extract_trailing_jummah(text)
    assert result is not None
    assert result["jummah1_iqamah"] == "1:00 PM"
    assert result["jummah2_iqamah"] == "1:45 PM"
    assert result["jummah3_iqamah"] == "2:30 PM"


def test_extract_trailing_jummah_returns_none_for_non_athanplus():
    """Parser returns None for texts that don't use the trailing-label layout."""
    for fname in ("numbered_jummah.txt", "khutbah_iqamah.txt", "unlabelled_jummah.txt"):
        text = clean_text((CASES_DIR / fname).read_text())
        assert extract_trailing_jummah(text) is None, f"Expected None for {fname}"


def test_extract_trailing_jummah_returns_none_on_disagreeing_blocks():
    """If two blocks have different Jummah times the function returns None."""
    block_a = "Jumuah 12:30 PM Jumuah 1 1:25 PM Jumuah 2 2:10 PM Jumuah 3"
    block_b = "Jumuah 1:00 PM Jumuah 1 1:45 PM Jumuah 2 2:30 PM Jumuah 3"
    text = f"Day 1 {block_a} Day 2 {block_b}"
    assert extract_trailing_jummah(text) is None


def test_to_prayer_fields_corrects_bad_aman_output():
    """to_prayer_fields with cleaned_text overrides the mis-paired LLM output."""
    import copy
    text = clean_text((CASES_DIR / "trailing_jummah_first_slot.txt").read_text())
    fields = to_prayer_fields(copy.deepcopy(_AMAN_BAD_LLM_JSON), cleaned_text=text)

    assert fields["jummah1_start"] is None
    assert fields["jummah1_iqamah"] == time(12, 30)
    assert fields["jummah2_start"] is None
    assert fields["jummah2_iqamah"] == time(13, 25)
    assert fields["jummah3_start"] is None
    assert fields["jummah3_iqamah"] == time(14, 10)


def test_to_prayer_fields_corrects_dropped_first_slot_nov24():
    """Replay the Nov 24 prod miss: 12:30 PM dropped, Jumuah 1 attached to 1:15 PM.

    The model read the labels as leading (Jumuah 1 -> 1:15 PM) and left
    12:30 PM with no slot, so the database stored jummah1=1:15 PM and
    jummah2=2:00 PM with jummah3 empty.
    """
    import copy
    bad = {
        "fajr_start": "5:58 AM", "fajr_iqamah": "6:30 AM",
        "zuhr_start": "12:04 PM", "zuhr_iqamah": "1:00 PM",
        "asr_start": "2:25 PM", "asr_iqamah": "3:15 PM",
        "maghrib_start": "4:45 PM", "maghrib_iqamah": "4:50 PM",
        "isha_start": "6:09 PM", "isha_iqamah": "7:00 PM",
        "jummah1_start": None, "jummah1_iqamah": "1:15 PM",
        "jummah2_start": None, "jummah2_iqamah": "2:00 PM",
        "jummah3_start": None, "jummah3_iqamah": None,
    }
    # Inline the cleaned Jummah section — parser doesn't need the full page.
    text = "Isha 6:09 PM 7:00 PM Jumuah 12:30 PM Jumuah 1 1:15 PM Jumuah 2 2:00 PM Jumuah 3 VIEW MONTHLY CALENDAR"
    fields = to_prayer_fields(copy.deepcopy(bad), cleaned_text=text)

    assert fields["jummah1_start"] is None
    assert fields["jummah1_iqamah"] == time(12, 30)
    assert fields["jummah2_start"] is None
    assert fields["jummah2_iqamah"] == time(13, 15)
    assert fields["jummah3_start"] is None
    assert fields["jummah3_iqamah"] == time(14, 0)


def test_to_prayer_fields_without_cleaned_text_uses_llm():
    """When cleaned_text is not passed, the LLM's Jummah fields are used as-is."""
    import copy
    # Bad LLM output has 12:30 PM as jummah1_start — this should NOT be fixed
    # when no cleaned_text is supplied.
    fields = to_prayer_fields(copy.deepcopy(_AMAN_BAD_LLM_JSON))
    # normalize_pair keeps jummah1_start because it is earlier than the iqamah
    assert fields["jummah1_start"] == time(12, 30)
    assert fields["jummah1_iqamah"] == time(13, 25)
