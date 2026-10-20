"""
Promptfoo Python provider for prayer-times LLM evals.

Runs the full production path: request_completion → parse_completion →
to_prayer_fields → serialized dict.  The model and per-token prices are taken
from the provider config block so the same file serves multiple providers.
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

from scraping.llm import OPENAI_MODEL, parse_completion, request_completion
from scraping.parsing import to_prayer_fields

INVALID_JSON_SENTINEL = "INVALID_JSON"


def _time_to_str(t):
    """Format a time object as 'H:MM AM/PM' (no leading zero on hour)."""
    if t is None:
        return None
    return t.strftime("%-I:%M %p")


def _compute_cost(usage, config: dict) -> float | None:
    """Return estimated USD cost from token usage and per-mtok prices in config."""
    input_price = config.get("input_price_per_mtok")
    output_price = config.get("output_price_per_mtok")
    if input_price is None or output_price is None:
        return None
    return (usage.prompt_tokens * input_price + usage.completion_tokens * output_price) / 1_000_000


def _token_usage(usage) -> dict:
    return {
        "prompt": usage.prompt_tokens,
        "completion": usage.completion_tokens,
        "total": usage.total_tokens,
    }


def call_api(prompt: str, options: dict, context: dict) -> dict:
    config = (options or {}).get("config") or {}
    model = config.get("model", OPENAI_MODEL)

    try:
        response = request_completion(prompt, model=model)
    except Exception as e:
        print(f"[OpenAI] Failed: {e}")
        return {"output": INVALID_JSON_SENTINEL}

    usage = response.usage
    result = {
        "tokenUsage": _token_usage(usage),
    }
    cost = _compute_cost(usage, config)
    if cost is not None:
        result["cost"] = cost

    llm_json = parse_completion(response)
    if llm_json is None:
        result["output"] = INVALID_JSON_SENTINEL
        return result

    fields = to_prayer_fields(llm_json)
    serialized = {k: _time_to_str(v) for k, v in fields.items()}
    result["output"] = json.dumps(serialized)
    return result
