from datetime import datetime


def test_to_dict_serializes_times_and_adds_utc_to_naive_timestamp(app, prayer_times_factory):
    from models.prayerTimes import PrayerTimes

    prayer_times_factory(mosque_name="Test Mosque", updated_at=datetime(2026, 10, 5, 3, 0, 0))

    with app.app_context():
        row = PrayerTimes.query.filter_by(mosque_name="Test Mosque").first()
        d = row.to_dict()

    assert d["fajr_start"] == "05:00:00"
    assert d["fajr_iqamah"] == "06:00:00"
    assert d["zuhr_start"] is None
    assert "+00:00" in d["updated_at"]
