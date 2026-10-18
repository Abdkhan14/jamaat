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

    return prayer_json
