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

# Same reasoning as gemini_client.py: server-side/rate-limit type errors
# are worth waiting out (total worst case here is about 5.5 minutes
# across 6 tries), but a 4xx that isn't a rate limit won't fix itself no
# matter how long you wait, so fail fast on those instead.
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
BACKOFF_SECONDS = [15, 30, 60, 90, 120, 120]


def generate_image(prompt: str, width: int = 1536, height: int = 1536, max_retries: int = 6) -> Image.Image:
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
        except requests.RequestException as e:
            last_error = str(e)
            if attempt < max_retries:
                wait = BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)]
                print(f"  Pollinations request errored ({e}) - retrying in {wait}s "
                      f"(attempt {attempt}/{max_retries})...")
                time.sleep(wait)
            continue

        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            return img.crop((0, 0, img.width, img.height - WATERMARK_STRIP_PX))

        # Capture the actual response body - a bare status code told us
        # nothing useful last time this failed.
        last_error = f"HTTP {resp.status_code}, content-type={resp.headers.get('content-type')}: {resp.text[:500]}"

        if resp.status_code not in RETRYABLE_STATUS_CODES:
            raise RuntimeError(f"Pollinations image call failed with a non-retryable error: {last_error}")

        if attempt < max_retries:
            wait = BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)]
            print(f"  Pollinations returned {resp.status_code} (likely temporary) - retrying in {wait}s "
                  f"(attempt {attempt}/{max_retries})...")
            time.sleep(wait)

    raise RuntimeError(f"Pollinations image call failed after {max_retries} attempts. Last error: {last_error}")
    
