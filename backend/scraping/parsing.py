import logging
import re
from datetime import datetime

DAILY_PRAYERS = ("fajr", "zuhr", "asr", "maghrib", "isha")
JUMMAH_SLOTS = ("jummah1", "jummah2", "jummah3")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AthanPlus trailing-label Jummah parser
#
# The AthanPlus widget renders Jummah as:
#   Jumuah <time1> Jumuah 1 <time2> Jumuah 2 <time3> Jumuah 3
# where every <timeN> is that slot's iqamah (no start times are shown).
#
# This regex matches the entire section in one pass on the cleaned text.
# It captures up to three times; unmatched optional groups are None.
# ---------------------------------------------------------------------------
_T = r"(\d{1,2}:\d{2} [AP]M)"
_J = r"Jum[a-z']*"

_TRAILING_JUMMAH = re.compile(
    rf"\b{_J}\s+{_T}\s+{_J}\s+1\b"
    rf"(?:\s+{_T}\s+{_J}\s+2\b)?"
    rf"(?:\s+{_T}\s+{_J}\s+3\b)?",
    re.IGNORECASE,
)


def extract_trailing_jummah(cleaned_text: str) -> dict | None:
    """
    Parse the AthanPlus trailing-label Jummah layout from cleaned text.

    Returns a dict with the six jummahN_start / jummahN_iqamah keys if the
    pattern is found and all day-blocks in the text agree on the same times.
    Returns None when:
      - the pattern is not found (not an AthanPlus-style widget), or
      - different day-blocks have different Jummah times (ambiguous which is
        today's block; let the LLM result stand).
    """
    matches = _TRAILING_JUMMAH.findall(cleaned_text)
    if not matches:
        return None

    # findall returns a list of group-tuples, e.g. [("12:30 PM","1:25 PM","2:10 PM"), ...]
    # Normalise empty-string optional groups to None.
    normalised = [tuple(g or None for g in m) for m in matches]

    # All blocks must agree.
    if len(set(normalised)) > 1:
        return None

    t1, t2, t3 = normalised[0]
    return {
        "jummah1_start": None, "jummah1_iqamah": t1,
        "jummah2_start": None, "jummah2_iqamah": t2,
        "jummah3_start": None, "jummah3_iqamah": t3,
    }


def format_time(value):
    if not value or value.strip().lower() in ["null", "none"]:
        return None

    try:
        dt = datetime.strptime(value.strip(), "%I:%M %p")
        return dt.time()
    except ValueError:
        return None


def normalize_prayer_times(prayer_json):
    def normalize_pair(start, iqamah):
        start_t, iqamah_t = format_time(start), format_time(iqamah)

        # Both times present but out of order → swap
        if start_t and iqamah_t and start_t >= iqamah_t:
            return iqamah, start

        # Only one time given → treat as iqamah
        if start_t and not iqamah_t:
            return None, start
        if iqamah_t and not start_t:
            return None, iqamah

        return start, iqamah

    for p in DAILY_PRAYERS:
        start_key, iqamah_key = f"{p}_start", f"{p}_iqamah"
        prayer_json[start_key], prayer_json[iqamah_key] = normalize_pair(
            prayer_json.get(start_key), prayer_json.get(iqamah_key)
        )

    # Sort Jummah slots by time (iqamah first, fall back to start), nulls last.
    # This corrects any out-of-order assignment the LLM may have made and also
    # ensures missing keys from the LLM become None rather than raising KeyError.
    def _slot_sort_key(slot_pair):
        start_str, iqamah_str = slot_pair
        t = format_time(iqamah_str) or format_time(start_str)
        # Slots with no time sort after all timed slots
        return (0, t) if t else (1, None)

    slots = [
        (prayer_json.get(f"jummah{n}_start"), prayer_json.get(f"jummah{n}_iqamah"))
        for n in (1, 2, 3)
    ]
    slots.sort(key=_slot_sort_key)

    for n, (start_val, iqamah_val) in enumerate(slots, start=1):
        prayer_json[f"jummah{n}_start"] = start_val
        prayer_json[f"jummah{n}_iqamah"] = iqamah_val

    return prayer_json


def to_prayer_fields(llm_json: dict, cleaned_text: str | None = None) -> dict:
    """Normalize and format all 16 prayer time fields from raw LLM JSON output.

    When cleaned_text is supplied, the AthanPlus trailing-label parser runs
    first. If it finds a confident match its Jummah times replace the LLM's
    Jummah keys before normalization, eliminating the ~1% mis-pairing that
    occurs when the LLM treats the first Jummah time as a start time.
    """
    if cleaned_text is not None:
        widget_slots = extract_trailing_jummah(cleaned_text)
        if widget_slots is not None:
            llm_jummah = {k: llm_json.get(k) for k in widget_slots}
            if llm_jummah != widget_slots:
                logger.info(
                    "Jummah slots taken from widget layout (LLM had: %s)",
                    {k: v for k, v in llm_jummah.items() if v},
                )
            llm_json = {**llm_json, **widget_slots}

    normalized = normalize_prayer_times(llm_json)

    daily = {
        f"{p}_{slot}": format_time(normalized[f"{p}_{slot}"])
        for p in DAILY_PRAYERS
        for slot in ("start", "iqamah")
    }
    jummah = {
        f"{slot}_{part}": format_time(normalized[f"{slot}_{part}"])
        for slot in JUMMAH_SLOTS
        for part in ("start", "iqamah")
    }
    return {**daily, **jummah}
