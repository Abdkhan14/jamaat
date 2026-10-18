from flask import Blueprint, jsonify
from models.prayerTimes import PrayerTimes
from mosques import MOSQUES

prayer_times_bp = Blueprint("prayer_times", __name__)


@prayer_times_bp.route("/prayer-times", methods=["GET"])
def get_prayer_times():
    times = PrayerTimes.query.all()
    times_serialized = [t.to_dict() for t in times]
    result = []

    for t in times_serialized:
        mosque = next((m for m in MOSQUES if m["name"] == t["mosque_name"]), None)
        if mosque:
            result.append({**mosque, "prayer_times": t})

    return jsonify(result)
