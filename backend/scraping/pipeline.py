import asyncio
import hashlib
from datetime import datetime, timezone

from config import EASTERN
from models.prayerTimes import PrayerTimes, db
from scraping.fetch import scrape_all_mosques
from scraping.llm import call_llm
from scraping.parsing import DAILY_PRAYERS, to_prayer_fields
from scraping.prompt import build_prompt
from scraping.text import TIME_PATTERN, clean_text


async def process_mosque(result):
    """Hash-check, call LLM, and return a PrayerTimes record or None."""
    cleaned_text = clean_text(result["raw_text"])

    content_hash = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()
    existing = db.session.get(PrayerTimes, result["name"])
    if existing and existing.raw_text_hash == content_hash:
        print(f"[skip] {result['name']} unchanged, skipping LLM")
        return None

    today = datetime.now(EASTERN)
    prompt = build_prompt(cleaned_text, today)

    llm_response_json = await asyncio.to_thread(call_llm, prompt)
    if not llm_response_json:
        return None

    if result.get("name") == "Masjid Al-Abedeen":
        with open("prompt_abedeen.txt", "w", encoding="utf-8") as f:
            f.write(prompt)

    fields = to_prayer_fields(llm_response_json)

    daily_values = [fields[f"{p}_{slot}"] for p in DAILY_PRAYERS for slot in ("start", "iqamah")]
    if all(v is None for v in daily_values):
        time_count = len(TIME_PATTERN.findall(cleaned_text))
        print(
            f"[reject] {result['name']} LLM returned only nulls, keeping existing data "
            f"(input: {len(cleaned_text)} chars, {time_count} time strings detected)"
        )
        return None

    return PrayerTimes(
        mosque_name=result["name"],
        date=today.date(),
        **fields,
        raw_text_hash=content_hash,
        updated_at=datetime.now(timezone.utc),
    )


async def run_all():
    """Scrape all mosques sequentially, then run all LLM calls concurrently."""
    scraped_results = await scrape_all_mosques()
    valid_results = [r for r in scraped_results if r]
    processed = await asyncio.gather(*[process_mosque(r) for r in valid_results])
    return [r for r in processed if r is not None]


def scrape_and_update(app):
    with app.app_context():
        print("Scrape job running...")

        records = asyncio.run(run_all())

        for record in records:
            db.session.merge(record)
        db.session.commit()

        print("Scrape job finished: data updated.")
