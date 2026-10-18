import re

# Matches any time string of the form "H:MM am/pm". Used to count time strings
# in scraped text for diagnostic logging when the LLM returns all-null times.
TIME_PATTERN = re.compile(r"\d{1,2}:\d{2}\s*[apAP]\.?[mM]")


def clean_text(raw):
    text = re.sub(r"[\n\t]+", " ", raw)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"([,.:])([^\s])", r"\1 \2", text)
    text = re.sub(r"(\d{1,2})\s*:\s*(\d{2})", r"\1:\2", text)
    text = re.sub(r"(\d{1,2}:\d{2})([apAP][mM])", r"\1 \2", text)
    text = re.sub(r"(\d{1,2}:\d{2})\s+([apAP])\s+([mM])\b", r"\1 \2\3", text)
    return text
