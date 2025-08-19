from flask import Flask, jsonify
from config import Config
from models.prayerTimes import db, PrayerTimes
from mosques import MOSQUES
from datetime import date, datetime, time

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    @app.route("/prayer-times", methods=["GET"])
    def get_prayer_times():
        times = PrayerTimes.query.all()
        times_serialized = [t.to_dict() for t in times]
        result = []

        for t in times_serialized:
            mosque = next((m for m in MOSQUES if m["name"] == t["mosque_name"]), None)
            if mosque:
                result.append(
                    {
                        **mosque,
                        "prayer_times": t
                    }
                )

        return jsonify(result)

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()  # ensure tables are created
    app.run(debug=True)
