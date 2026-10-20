import json
import logging
import os

from openai import OpenAI

OPENAI_MODEL = "gpt-5.1"
MAX_COMPLETION_TOKENS = 500
LLM_TIMEOUT = 30
SYSTEM_MESSAGE = "You are a helpful assistant that only outputs valid JSON objects."
RESPONSE_PREVIEW_CHARS = 500

logger = logging.getLogger(__name__)

# Created on import: load_dotenv() in app.py must run before this module is imported.
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def request_completion(prompt: str, model: str = OPENAI_MODEL):
    """Send the prompt and return the raw OpenAI response (including usage)."""
    return client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": prompt},
        ],
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        top_p=1,
        timeout=LLM_TIMEOUT,
    )


def completion_text(response) -> str:
    try:
        return response.choices[0].message.content or ""
    except (AttributeError, IndexError):
        return ""


def parse_completion(response) -> dict | None:
    """Extract and JSON-parse the content from a completion response."""
    try:
        return json.loads(completion_text(response))
    except Exception:
        return None


def call_llm(prompt: str, model: str = OPENAI_MODEL) -> dict | None:
    try:
        response = request_completion(prompt, model=model)
    except Exception:
        logger.exception("OpenAI request failed", extra={"model": model})
        return None

    result = parse_completion(response)
    if result is None:
        logger.error(
            "OpenAI response was not valid JSON",
            extra={"model": model, "response_preview": completion_text(response)[:RESPONSE_PREVIEW_CHARS]},
        )
    return result
