import json
import os

from openai import OpenAI

OPENAI_MODEL = "gpt-5.1"
MAX_COMPLETION_TOKENS = 500
LLM_TIMEOUT = 30

# Created on import: load_dotenv() in app.py must run before this module is imported.
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def call_llm(prompt: str):
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only outputs valid JSON objects."},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=MAX_COMPLETION_TOKENS,
            top_p=1,
            timeout=LLM_TIMEOUT,
        )

        choice = response.choices[0].message.content
        return json.loads(choice)

    except Exception as e:
        print(f"[OpenAI] Failed: {e}")
        return None
