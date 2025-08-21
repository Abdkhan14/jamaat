from socket import timeout
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import httpx
import asyncio
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from config import Config
from models.prayerTimes import db, PrayerTimes
from mosques import MOSQUES
from datetime import date, datetime, time
import atexit
import json
from openai import OpenAI

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

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

    def call_llm(prompt: str):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",  # fast & cheaper model; you can use "gpt-4o" too
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that only outputs valid JSON objects."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.0,
                top_p=1.0,
                response_format={"type": "json_object"},  # ✅ ensures valid JSON
            )

            choice = response.choices[0].message.content
            return json.loads(choice)

        except Exception as e:
            return None

    async def scrape_mosque(client, mosque):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/115.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            response = await client.get(mosque["website"], timeout=120.0, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            return {
                **mosque,
                "raw_text": text
            }
        except Exception as e:
            return None

    async def scrape_all_mosques():
        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [scrape_mosque(client, m) for m in MOSQUES]
            return await asyncio.gather(*tasks)

    def format_time(value):
        if not value or value.strip().lower() in ["null", "none"] :
            return None

        try:
            dt = datetime.strptime(value.strip(), "%I:%M %p")
            return dt.time()
        except ValueError:
            return None

    def normalize_prayer_times(prayer_json):
        def normalize_pair(start, iqamah):
            start_t, iqamah_t = format_time(start), format_time(iqamah)

            # Case 1: both times present but out of order → fix
            if start_t and iqamah_t and start_t >= iqamah_t:
                # swap if clearly reversed
                return iqamah, start

            # Case 2: only one time given → assume iqamah
            if start_t and not iqamah_t:
                return None, start
            if iqamah_t and not start_t:
                return None, iqamah

            # Case 3: both null → leave as is
            return start, iqamah

        # Apply to all 5 daily prayers
        for p in ["fajr", "zuhr", "asr", "maghrib", "isha"]:
            start_key, iqamah_key = f"{p}_start", f"{p}_iqamah"
            prayer_json[start_key], prayer_json[iqamah_key] = normalize_pair(
                prayer_json.get(start_key), prayer_json.get(iqamah_key)
            )

        return prayer_json

    def scrape_and_update():
        with app.app_context():
            print("Mock job running: scraping + LLM simulation...")

            records = []
            scraped_results = asyncio.run(scrape_all_mosques())
            for result in scraped_results:
                if result: 
                    raw_text = result["raw_text"]
                    prompt = f"""
                    Extract the prayer times from the following text.

                    - Prayer times must be copied exactly as written in the text (e.g., "10:00 PM" stays "10:00 PM").
                    - Do not round, adjust, or guess times.
                    - If multiple times are present for the same prayer, still apply the earliest= start, latest= iqamah rule,
                    but the values themselves must be identical to the original text. 
                    - Prayer names may have different spellings (e.g., "Fajr" → "Fajar", "Maghrib" → "Magrib").
                    - {{prayer}}_start usually refers to *adhan* / *begins* / *khutbah* / *azan* etc.
                    - {{prayer}}_iqamah refers to the later congregational prayer time (*salah* / *salat*).
                    - If multiple times are listed for the same prayer, use the **earliest** as {{prayer}}_start
                    and the **latest** as {{prayer}}_iqamah.
                    - ⚠️ If **only one time** is mentioned for a prayer, assign the value to {{prayer}}_iqamah and set
                    {{prayer}}_start = null. 
                    - If you can't find a valid time for a prayer, (ex: sometimes Maghrib times are represented as 'sunset' 
                    in websites) set the value = null.
                    
                    - Only move on to jummah timings once you have completed evaluating values for fajr, zuhr, asr, maghrib and isha.
                    - Jummmah (Friday) prayer can have up to 3 slots: jummah1, jummah2, jummah3.
                    - Jummah (Friday) prayer times:
                        - After assigning Fajr, Zuhr, Asr, Maghrib, and Isha, re-check the text for any times between 12:00 PM and 5:00 PM.
                        - ALL times in that range, near other jummah timings, must be treated as Jummah times, even if not labeled with the word "Jummah" or
                        it's alternate spellings.
                        - Collect all valid Jummah times, sort them ascending, then distribute using the following pattern:
                            * 1 time → jummah1_iqamah only (start = null).
                            * 2 to 5 times → assign left to right as start/iqamah pairs; if odd (3) or (5), last one is iqamah only.
                            * 6 times → assign as 3 full start/iqamah pairs.
                        - Within a pair, the earlier = start, later = iqamah.
                        - If no times exist in the range, set all Jummah fields to null.
                        - Special case for jummah (do NOT output this example, it is only to guide you):
                        - If the input text contains:
                            Fajr 5:08 AM 6:00 AM  
                            Dhuhr 1:19 PM 2:00 PM  
                            Asr 6:05 PM 6:45 PM  
                            Maghrib 8:04 PM 8:08 PM  
                            Isha 9:30 PM 10:00 PM  
                            1:45 PM 
                            Jumu'ah 
                            2:45 PM 
                            Jumu'ah 
                            3:45 PM 
                            Jumu'ah 
                            6:33 AM 
                            8:04 PM
                        - Then the correct output must include:
                            "jummah1_iqamah": "1:45 PM",  
                            "jummah2_iqamah": "2:45 PM",  
                            "jummah3_iqamah": "3:45 PM"
                        - Just notice how I considered 1:45 PM as a valid jummah time, ONLY because it's in jummah time range, near other jummah timings,
                        even though it's not tied to a specific jummah word following the pattern.

                    Return ONLY valid JSON in this exact schema, no explanation:

                    {{
                        "fajr_start": "HH:MM AM/PM or null",
                        "fajr_iqamah": "...",
                        "zuhr_start": "...",
                        "zuhr_iqamah": "...",
                        "asr_start": "...",
                        "asr_iqamah": "...",
                        "maghrib_start": "...",
                        "maghrib_iqamah": "...",
                        "isha_start": "...",
                        "isha_iqamah": "...",
                        "jummah1_start": "...",
                        "jummah1_iqamah": "...",
                        "jummah2_start": "...",
                        "jummah2_iqamah": "...",
                        "jummah3_start": "...",
                        "jummah3_iqamah": "..."
                    }}

                    Text:
                    ---
                    {raw_text}
                    ---
                    """
                    
                    llm_response_json = call_llm(prompt)

                    if llm_response_json: 
                        normalized_llm_response = normalize_prayer_times(llm_response_json)

                        records.append(
                            PrayerTimes(
                                mosque_name=result["name"],
                                date=date.today(),
                                fajr_start=format_time(normalized_llm_response["fajr_start"]),
                                fajr_iqamah=format_time(normalized_llm_response["fajr_iqamah"]),
                                zuhr_start=format_time(normalized_llm_response["zuhr_start"]),
                                zuhr_iqamah=format_time(normalized_llm_response["zuhr_iqamah"]),
                                asr_start=format_time(normalized_llm_response["asr_start"]),
                                asr_iqamah=format_time(normalized_llm_response["asr_iqamah"]),
                                maghrib_start=format_time(normalized_llm_response["maghrib_start"]),
                                maghrib_iqamah=format_time(normalized_llm_response["maghrib_iqamah"]),
                                isha_start=format_time(normalized_llm_response["isha_start"]),
                                isha_iqamah=format_time(normalized_llm_response["isha_iqamah"]),
                                jummah1_start=format_time(normalized_llm_response["jummah1_start"]),
                                jummah1_iqamah=format_time(normalized_llm_response["jummah1_iqamah"]),
                                jummah2_start=format_time(normalized_llm_response["jummah2_start"]),
                                jummah2_iqamah=format_time(normalized_llm_response["jummah2_iqamah"]),
                                jummah3_start=format_time(normalized_llm_response["jummah3_start"]),
                                jummah3_iqamah=format_time(normalized_llm_response["jummah3_iqamah"]),
                                updated_at=datetime.now()
                            ),
                        )

            
            for record in records:
                db.session.merge(record) 
            db.session.commit()

            print("Mock job finished: data updated.")

    # --- Scheduler setup ---
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scrape_and_update, trigger="interval", hours=24)
    scheduler.start()

    # Ensure scheduler shuts down with Flask
    atexit.register(lambda: scheduler.shutdown())

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()  # ensure tables are created
    app.run()
