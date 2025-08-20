from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import httpx
import asyncio
from bs4 import BeautifulSoup
from config import Config
from models.prayerTimes import db, PrayerTimes
from mosques import MOSQUES
from datetime import date, datetime, time
import atexit

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

    async def scrape_mosque(client, mosque):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/115.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            response = await client.get(mosque["website"], timeout=20.0, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            return {
                "mosque": mosque["name"],
                "url": mosque["website"],
                "status": "success",
                "preview": text[:200]
            }
        except Exception as e:
            return {
                "mosque": mosque["name"],
                "url": mosque["website"],
                "status": "error",
                "message": str(e)
            }

    async def scrape_all_mosques():
        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [scrape_mosque(client, m) for m in MOSQUES]
            return await asyncio.gather(*tasks)

    def scrape_and_update():
        with app.app_context():
            print("Mock job running: scraping + LLM simulation...")

            scraped_results = asyncio.run(scrape_all_mosques())

            # Just overwrite the table for now
            PrayerTimes.query.delete()

            records = [
                PrayerTimes(
                    mosque_name="Baitul Aman",
                    date=date.today(),
                    fajr_start=time(5, 0),
                    fajr_iqamah=time(5, 30),
                    zuhr_start=time(13, 0),
                    zuhr_iqamah=time(13, 30),
                    asr_start=time(17, 0),
                    asr_iqamah=time(17, 30),
                    maghrib_start=time(20, 15),
                    maghrib_iqamah=time(20, 20),
                    isha_start=time(21, 30),
                    isha_iqamah=time(22, 0),
                    jummah1_start=time(13, 15),
                    jummah1_iqamah=time(13, 30),
                    updated_at=datetime.now()
                ),
                PrayerTimes(
                    mosque_name="Baitul Mukarram",
                    date=date.today(),
                    fajr_start=time(5, 5),
                    fajr_iqamah=time(5, 35),
                    zuhr_start=time(13, 5),
                    zuhr_iqamah=time(13, 35),
                    asr_start=time(17, 5),
                    asr_iqamah=time(17, 35),
                    maghrib_start=time(20, 20),
                    maghrib_iqamah=time(20, 25),
                    isha_start=time(21, 35),
                    isha_iqamah=time(22, 5),
                    jummah1_start=time(13, 20),
                    jummah1_iqamah=time(13, 40),
                    updated_at=datetime.now()
                )
            ]

            for record in records:
                db.session.merge(record)  # insert or update
            db.session.commit()

            print("Mock job finished: data updated.")

    # --- Scheduler setup ---
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scrape_and_update, trigger="interval", seconds=10)
    scheduler.start()

    # Ensure scheduler shuts down with Flask
    atexit.register(lambda: scheduler.shutdown())

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()  # ensure tables are created
    app.run(debug=True)
