from datetime import datetime

DAILY_PRAYERS = ("fajr", "zuhr", "asr", "maghrib", "isha")
JUMMAH_SLOTS = ("jummah1", "jummah2", "jummah3")


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


def to_prayer_fields(llm_json: dict) -> dict:
    """Normalize and format all 16 prayer time fields from raw LLM JSON output."""
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
