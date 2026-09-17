"""
Minimal wrapper around Google's Gemini API - just the two calls this
pipeline needs: generate_text() and generate_image().

No SDK dependency on purpose (fewer things to break) - just plain requests
calls against the public REST endpoint.
"""

import base64
import io
import json
import time

import requests
from PIL import Image

import config

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _post(model: str, payload: dict, max_retries: int = 3) -> dict:
    url = f"{BASE_URL}/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": config.GEMINI_API_KEY}

    last_error = None
    for attempt in range(1, max_retries + 1):
        resp = requests.post(url, headers=headers, params=params, json=payload, timeout=120)
        if resp.status_code == 200:
            return resp.json()
        last_error = f"HTTP {resp.status_code}: {resp.text[:500]}"
        # back off and retry - covers transient rate limits / hiccups
        time.sleep(5 * attempt)
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


def generate_image(prompt: str) -> Image.Image:
    """Returns a PIL Image for an image-generation prompt."""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = _post(config.IMAGE_MODEL, payload)
    parts = data["candidates"][0]["content"]["parts"]
    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            image_bytes = base64.b64decode(inline["data"])
            return Image.open(io.BytesIO(image_bytes)).convert("RGB")
    raise RuntimeError(f"No image data in Gemini response: {data}")
