"""
Promptfoo prompt functions for LLM evals.

Each function takes a promptfoo context dict and returns the full prompt string.
Add candidate prompt functions here when comparing alternatives.
"""

import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from datetime import date

from scraping.prompt import build_prompt
from scraping.text import clean_text


def current(context: dict) -> str:
    """Production prompt: clean_text → build_prompt with the case's today date."""
    vars_ = context["vars"]
    cleaned = clean_text(vars_["text"])
    today = date.fromisoformat(vars_["today"])
    return build_prompt(cleaned, today)
