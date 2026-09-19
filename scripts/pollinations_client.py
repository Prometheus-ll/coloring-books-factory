"""
Image generation via Pollinations.ai - free, key-less (no signup, no auth
header, just a GET request).

Crops off Pollinations' watermark strip: `nologo=true` only works with a
registered, authenticated key (see README) - anonymous requests get
stamped regardless. Cheapest fix that needs no signup: ask for a bit of
extra height and crop the strip off before anything else touches the
image.

Returns the color image as-is - generate_book.py decides whether to run
it through lineart_processor (interior pages) or keep it in color (the
cover, and the small reference thumbnail on each interior page).
"""

import io
import time
import urllib.parse

import requests
from PIL import Image

import config

BASE_URL = "https://image.pollinations.ai/prompt"
WATERMARK_STRIP_PX = 80


def generate_image(prompt: str, width: int = 1536, height: int = 1536, max_retries: int = 3) -> Image.Image:
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"{BASE_URL}/{encoded_prompt}"
    params = {
        "width": width,
        "height": height + WATERMARK_STRIP_PX,
        "model": config.POLLINATIONS_IMAGE_MODEL,
        "nologo": "true",  # harmless to leave in even though it needs auth to actually work
        "seed": int(time.time() * 1000) % 1_000_000,
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=180)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                return img.crop((0, 0, img.width, img.height - WATERMARK_STRIP_PX))
            last_error = f"HTTP {resp.status_code}, content-type={resp.headers.get('content-type')}"
        except requests.RequestException as e:
            last_error = str(e)
        time.sleep(5 * attempt)

    raise RuntimeError(f"Pollinations image call failed after {max_retries} attempts. Last error: {last_error}")
