from socket import timeout
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
import os
from dotenv import load_dotenv
from config import Config
from models.prayerTimes import db, PrayerTimes
from mosques import MOSQUES
from datetime import date, datetime, time
import atexit
import json
from openai import OpenAI
from flask_cors import CORS
import re
from playwright.async_api import async_playwright


# Load environment variables from a .env file
load_dotenv()

# Initialize OpenAI client with API key from environment
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def create_app():
    # Create Flask app instance
    app = Flask(__name__)
    
    CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})
    
    # Load configuration from Config object
    app.config.from_object(Config)

    # Initialize SQLAlchemy with Flask app
    db.init_app(app)

    # Define route to get all prayer times
    @app.route("/prayer-times", methods=["GET"])
    def get_prayer_times():
        # Query all prayer times from the database
        times = PrayerTimes.query.all()
        # Serialize each PrayerTimes object to dict
        times_serialized = [t.to_dict() for t in times]
        result = []

        # Merge mosque info with corresponding prayer times
        for t in times_serialized:
            mosque = next((m for m in MOSQUES if m["name"] == t["mosque_name"]), None)
            if mosque:
                result.append(
                    {
                        **mosque,
                        "prayer_times": t
                    }
                )

        # Return the result as JSON
        return jsonify(result)

    # Function to call the OpenAI LLM with a prompt and return parsed JSON
    def call_llm(prompt: str):
        try:
            response = client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that only outputs valid JSON objects."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.0,
                top_p=1.0,
                response_format={"type": "json_object"}, 
            )

            choice = response.choices[0].message.content
            return json.loads(choice)

        except Exception as e:
            # Return None if any error occurs
            return None

    async def scrape_mosque_playwright(mosque):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled"
                    ]
                )

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36",
                    locale="en-US",
                    timezone_id="America/Toronto"
                )

                page = await context.new_page()
                await page.goto(mosque["website"], timeout=120_000)

                # Wait for page to settle (JS-rendered content)
                await page.wait_for_load_state("networkidle")

                # Get visible text only
                text = await page.evaluate("""
                    () => {
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            {
                                acceptNode: (node) => {
                                    if (!node.parentElement) return NodeFilter.FILTER_REJECT;
                                    const style = window.getComputedStyle(node.parentElement);
                                    if (style.display === "none" || style.visibility === "hidden") {
                                        return NodeFilter.FILTER_REJECT;
                                    }
                                    return NodeFilter.FILTER_ACCEPT;
                                }
                            }
                        );

                        let content = [];
                        while (walker.nextNode()) {
                            const value = walker.currentNode.nodeValue.trim();
                            if (value.length > 0) content.push(value);
                        }
                        return content.join("\\n");
                    }
                """)

                await browser.close()

                return {
                    **mosque,
                    "raw_text": text
                }

        except Exception as e:
            print(f"[Playwright] Failed for {mosque['name']}: {e}")
            return None

    # Asynchronous function to scrape all mosques in parallel
    async def scrape_all_mosques():
        tasks = [scrape_mosque_playwright(m) for m in MOSQUES]
        return await asyncio.gather(*tasks)

    # Helper function to parse and format time strings
    def format_time(value):
        if not value or value.strip().lower() in ["null", "none"] :
            return None

        try:
            dt = datetime.strptime(value.strip(), "%I:%M %p")
            return dt.time()
        except ValueError:
            return None

    # Normalize prayer times to ensure correct start/iqamah assignment
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

        # Apply normalization to all 5 daily prayers
        for p in ["fajr", "zuhr", "asr", "maghrib", "isha"]:
            start_key, iqamah_key = f"{p}_start", f"{p}_iqamah"
            prayer_json[start_key], prayer_json[iqamah_key] = normalize_pair(
                prayer_json.get(start_key), prayer_json.get(iqamah_key)
            )

        return prayer_json
   
    def clean_text(raw):
        # Normalize line breaks and spacing
        text = " ".join(raw.split())

        # Ensure space after commas
        text = text.replace(",", ", ")

        # Fix broken time splits like "2\n:30"
        text = re.sub(r"(\d)\s*:\s*(\d+)", r"\1:\2", text)

        return text

    # Main function to scrape, extract, normalize, and update prayer times in the database
    def scrape_and_update():
        with app.app_context():
            print("Mock job running: scraping + LLM simulation...")

            records = []
            # Scrape all mosques asynchronously
            scraped_results = asyncio.run(scrape_all_mosques())
            for result in scraped_results:
                if result: 
                    cleaned_text = clean_text(result["raw_text"])
                    # Compose prompt for LLM to extract prayer times
                    prompt = f"""
                    Extract the prayer times from the following text.

                    - Prayer times must be copied exactly as written in the text (e.g., "10:00 PM" stays "10:00 PM").
                    - Do not round, adjust, or guess times.
                    - If multiple times are present for the same prayer, still apply the earliest= start, latest= iqamah rule,
                    but the values themselves must be identical to the original text. 
                    - Prayer names may have different spellings (e.g., "Fajr" → "Fajar", "Maghrib" → "Magrib").
                    - {{prayer}}_start is also referred as *adhan* / *begins* / *khutbah* / *azan* etc. 
                    - {{prayer}}_iqamah refers to the later congregational prayer time (*salah* / *salat*).
                    - If multiple times are listed for the same prayer, use the **earliest** as {{prayer}}_start
                    and the **latest** as {{prayer}}_iqamah.
                    - ⚠️ If **only one time** is mentioned for a prayer, assign the value to {{prayer}}_iqamah and set
                    {{prayer}}_start = null. 
                    - ⚠️ Sometimes times are joined directly with words without spaces (e.g., "Khutbah1:30pm" or "Iqamah2:00pm").
                    In such cases, you must still detect and extract the time exactly as written ("1:30pm", "2:00pm").
                     Do not ignore times just because they are attached to words.
                    - ⚠️ Sometimes times are broken by newlines or irregular spacing (e.g.,
                    "6\n:30\npm" should be understood as "6:30 pm").
                    You must normalize and extract the correct time string exactly as written, without losing AM/PM.
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
                        - If a Jummah slot is written as Khutbah X:XX followed by Iqamah Y:YY and there can be commas not seperated by spaces, then 
                        Khutbah time must always be the start and Iqamah time the iqamah, even if the text is irregularly formatted.
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
                        * If a line contains both "Khutbah" and "Iqamah" times, always map:
                        - The Khutbah time → jummahN_start
                        - The Iqamah time → jummahN_iqamah
                        * This rule applies even if the Khutbah time is joined to the word (e.g., "Khutbah1:30pm")
                            or split across lines (e.g., "1\n:30 pm").
                        * Do not skip Khutbah times. They must always be extracted as the start time.

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
                    {cleaned_text}
                    ---
                    """
                    
                    # Call LLM to extract prayer times from raw text
                    llm_response_json = call_llm(prompt)

                    if llm_response_json: 
                        # Normalize the LLM response for consistency
                        normalized_llm_response = normalize_prayer_times(llm_response_json)

                        # Create a new PrayerTimes record from normalized data
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

            # Merge (upsert) all new records into the database
            for record in records:
                db.session.merge(record) 
            db.session.commit()

            print("Mock job finished: data updated.")

    # --- Scheduler setup ---
    # Create a background scheduler to run scrape_and_update periodically
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scrape_and_update, trigger="interval", hours=30)
    scheduler.start()

    # Ensure scheduler shuts down with Flask
    atexit.register(lambda: scheduler.shutdown())

    return app

# Run the Flask app if this file is executed directly
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()  # ensure tables are created
    app.run()
