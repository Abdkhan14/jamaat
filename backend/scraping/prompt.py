from datetime import datetime

from config import EASTERN

PROMPT_TEMPLATE = """
                Extract the prayer times from the following text.

                TODAY'S DATE: {today}

                - Some pages list prayer times for SEVERAL DAYS at once (a weekly/monthly calendar, or
                the same set of prayers repeated once per day). In that case, extract ONLY the block or
                row belonging to TODAY'S DATE above, and ignore every other date.
                - If the text repeats several similar day-blocks but none of them is labelled with a date
                you can match to today, use the FIRST block and treat the rest as duplicates to ignore.
                - If the text only covers a single day (no dates, or one date), ignore the two rules above
                and extract the times normally.

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
                    - ⚠️ NEVER reuse a time already assigned to Fajr, Zuhr, Asr, Maghrib or Isha as a Jummah time.
                    - ⚠️ Only fill Jummah fields if the text explicitly mentions Jummah / Jumu'ah / Jumuah / Friday prayer / Khutbah,
                    or has unlabelled 12-5 PM times directly adjacent to those words. If none of those words appear,
                    set every Jummah field to null — even if TODAY'S DATE is a Friday.
                    - ALL times in that range, near other jummah timings, must be treated as Jummah times, even if not labeled with the word "Jummah" or
                    it's alternate spellings.
                    - PRIORITY RULE — Numbered slot labels (apply BEFORE the count-based pairing rule below):
                        * If each Jummah time is accompanied by an explicit numbered slot label such as
                          "Jumuah 1" / "Jumuah 2" / "Jumuah 3",
                          "Jamat 1" / "Jamat 2" / "Jamat 3",
                          "1st Jamat" / "2nd Jamat" / "3rd Jamat",
                          "Jumu'ah 1" / "1st Jumu'ah" / etc.,
                          then each labeled time is its OWN iqamah. Map directly:
                            - slot-1 label → jummah1_iqamah
                            - slot-2 label → jummah2_iqamah
                            - slot-3 label → jummah3_iqamah
                          Set jummahN_start = null UNLESS that time is also explicitly preceded by
                          "Khutbah" / "Adhan" / "Azan" / "Begins" (in which case the start/iqamah pairing applies for that single slot).
                        * SKIP the "2–5 times → pairs" distribution rule entirely when numbered slot labels are present.
                    - Count-based pairing (only applies when numbered slot labels are NOT present):
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


def build_prompt(cleaned_text: str, today: datetime) -> str:
    # Day is built without strftime's zero-padding so it matches how sites write dates.
    today_label = f"{today:%A, %B} {today.day}, {today:%Y}"
    return PROMPT_TEMPLATE.format(cleaned_text=cleaned_text, today=today_label)
