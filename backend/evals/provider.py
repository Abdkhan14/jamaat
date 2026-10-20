"""
Promptfoo Python provider for prayer-times LLM evals.

Runs the full production path: call_llm → to_prayer_fields → serialized dict.
The model is taken from the provider's config block so the same file serves
multiple providers (gpt-5.1, gpt-5-mini, etc.) without duplication.
"""

import json
import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# Must run before importing scraping.llm — the OpenAI client is created on import
from dotenv import load_dotenv
load_dotenv(os.path.join(_BACKEND_DIR, ".env"))

from scraping.llm import OPENAI_MODEL, call_llm
from scraping.parsing import to_prayer_fields

INVALID_JSON_SENTINEL = "INVALID_JSON"


def _time_to_str(t):
    """Format a time object as 'H:MM AM/PM' (no leading zero on hour)."""
    if t is None:
        return None
    return t.strftime("%-I:%M %p")


def call_api(prompt: str, options: dict, context: dict) -> dict:
    config = (options or {}).get("config") or {}
    model = config.get("model", OPENAI_MODEL)

    llm_json = call_llm(prompt, model=model)
    if llm_json is None:
        return {"output": INVALID_JSON_SENTINEL}

    fields = to_prayer_fields(llm_json)
    serialized = {k: _time_to_str(v) for k, v in fields.items()}
    return {"output": json.dumps(serialized)}
