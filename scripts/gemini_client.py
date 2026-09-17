"""
Minimal wrapper around Google's Gemini API for text generation
(generate_text / generate_json). Image generation lives in
pollinations_client.py instead - see config.py for why.

No SDK dependency on purpose (fewer things to break) - just plain requests
calls against the public REST endpoint.
"""

import json
import time

import requests

import config

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
# Total worst case here is about 5.5 minutes of waiting, spread across 6
# tries - generous on purpose, since a demand spike can outlast a quick
# retry. Codes outside RETRYABLE_STATUS_CODES (bad model name, bad
# request, auth problems) fail immediately instead - those won't fix
# themselves no matter how long you wait.
BACKOFF_SECONDS = [15, 30, 60, 90, 120, 120]


def _post(model: str, payload: dict, max_retries: int = 6) -> dict:
    url = f"{BASE_URL}/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": config.GEMINI_API_KEY}

    last_error = None
    for attempt in range(1, max_retries + 1):
        resp = requests.post(url, headers=headers, params=params, json=payload, timeout=120)
        if resp.status_code == 200:
            return resp.json()

        last_error = f"HTTP {resp.status_code}: {resp.text[:500]}"

        if resp.status_code not in RETRYABLE_STATUS_CODES:
            raise RuntimeError(f"Gemini call to {model} failed with a non-retryable error: {last_error}")

        if attempt < max_retries:
            wait = BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)]
            print(f"  Gemini returned {resp.status_code} (likely temporary) - retrying in {wait}s "
                  f"(attempt {attempt}/{max_retries})...")
            time.sleep(wait)

    raise RuntimeError(f"Gemini call to {model} failed after {max_retries} attempts. Last error: {last_error}")


def generate_text(prompt: str) -> str:
    """Returns the raw text response for a prompt."""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = _post(config.TEXT_MODEL, payload)
    parts = data["candidates"][0]["content"]["parts"]
    text_parts = [p["text"] for p in parts if "text" in p]
    if not text_parts:
        raise RuntimeError(f"No text in Gemini response: {data}")
    return "".join(text_parts)


def generate_json(prompt: str) -> dict:
    """
    Asks for JSON and parses it. Strips ```json fences if the model adds
    them despite being told not to (it sometimes does).
    """
    raw = generate_text(prompt)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Could not parse JSON from Gemini text response.\nRaw response:\n{raw}") from e
        
