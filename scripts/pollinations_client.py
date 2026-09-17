"""
Image generation via Pollinations.ai - a genuinely free, key-less image API
(no signup, no auth header, just a GET request). This replaced Gemini's
image models, which no longer have a working free API tier.

Trade-off vs a paid model: output can occasionally carry a small watermark
and is less consistent than Nano Banana / Nano Banana 2. For a $0 hobby
pipeline that's the right trade; if quality becomes the bottleneck later,
swap this module for a paid call and nothing else in the pipeline changes.
"""

import io
import time
import urllib.parse

import requests
from PIL import Image

import config

BASE_URL = "https://image.pollinations.ai/prompt"


def generate_image(prompt: str, width: int = 1024, height: int = 1024, max_retries: int = 3) -> Image.Image:
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"{BASE_URL}/{encoded_prompt}"
    params = {
        "width": width,
        "height": height,
        "model": config.POLLINATIONS_IMAGE_MODEL,
        "nologo": "true",
        # A random-ish seed keeps consecutive pages from coming back near-identical.
        "seed": int(time.time() * 1000) % 1_000_000,
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=180)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
                return Image.open(io.BytesIO(resp.content)).convert("RGB")
            last_error = f"HTTP {resp.status_code}, content-type={resp.headers.get('content-type')}"
        except requests.RequestException as e:
            last_error = str(e)
        time.sleep(5 * attempt)

    raise RuntimeError(f"Pollinations image call failed after {max_retries} attempts. Last error: {last_error}")
