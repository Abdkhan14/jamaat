"""
Promptfoo Python assertion scorer for prayer-times evals.

Compares provider output (serialized to_prayer_fields dict) against the
expected JSON fixture, field by field, using format_time for normalization
so minor string differences (case, whitespace) don't count as errors.
"""

import json
import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from scraping.parsing import DAILY_PRAYERS, JUMMAH_SLOTS, format_time

FIELDS = (
    [f"{p}_{slot}" for p in DAILY_PRAYERS for slot in ("start", "iqamah")]
    + [f"{slot}_{part}" for slot in JUMMAH_SLOTS for part in ("start", "iqamah")]
)

INVALID_JSON_SENTINEL = "INVALID_JSON"


def get_score(output: str, context: dict) -> dict:
    expected_raw = json.loads(context["vars"]["expected"])

    if output == INVALID_JSON_SENTINEL:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "LLM returned invalid JSON",
            "namedScores": {
                "field_accuracy": 0.0,
                "hallucinations": 0,
                "valid_json": 0.0,
            },
        }

    actual_raw = json.loads(output)

    correct = 0
    hallucinations = 0
    wrong_fields = []

    for field in FIELDS:
        expected_val = format_time(expected_raw.get(field))
        actual_val = format_time(actual_raw.get(field))

        if expected_val == actual_val:
            correct += 1
        else:
            wrong_fields.append(
                f"{field}: expected {expected_raw.get(field)!r}, got {actual_raw.get(field)!r}"
            )
        if expected_val is None and actual_val is not None:
            hallucinations += 1

    field_accuracy = correct / len(FIELDS)
    reason = (
        f"{correct}/{len(FIELDS)} fields correct"
        + (f" — wrong: {'; '.join(wrong_fields)}" if wrong_fields else "")
    )

    return {
        "pass": correct == len(FIELDS),
        "score": field_accuracy,
        "reason": reason,
        "namedScores": {
            "field_accuracy": field_accuracy,
            "hallucinations": hallucinations,
            "valid_json": 1.0,
        },
    }
