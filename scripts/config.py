"""
All the settings you're likely to want to tweak live here, in one place.
Nothing in this file is secret - API keys come from environment variables
(set as GitHub Actions secrets), never hardcoded here.
"""

import os

# ---- Brand ----
SHOP_NAME = "DoodleDrop"

# ---- Content ----
NUM_INTERIOR_PAGES = 12          # how many coloring pages per book (not counting cover)
AUDIENCE_HINT = "all ages (kids and adults)"

# ---- Output look ----
PAGE_WIDTH_PX = 2550             # 8.5in x 300dpi
PAGE_HEIGHT_PX = 3300            # 11in x 300dpi
MARGIN_PX = 150
PAGE_NUMBER_FONT_SIZE = 40
COVER_TITLE_FONT_SIZE = 120
COVER_SUBTITLE_FONT_SIZE = 55

# ---- Pricing ----
# Simple fixed price to start. Change this any time - it's not AI-decided
# on purpose, so it stays predictable.
PRICE_USD = 4.99

# ---- Gemini model (text only - see note below on images) ----
# gemini-2.5-flash was retired for new callers; this is its current
# replacement. If Google moves the goalposts again, this is the one line
# to change - and it's worth checking ai.google.dev/gemini-api/docs/pricing
# for "Deprecated" warnings every so often, since this has now happened twice.
TEXT_MODEL = "gemini-3.6-flash"

# ---- Image generation ----
# IMPORTANT: Gemini's image models (Nano Banana / Nano Banana 2) do not
# have a working free API tier - the "500 free images/day" this project
# started with turned out to be a since-expired hackathon promotion, not
# a standing feature. Images are generated via Pollinations.ai instead
# (see pollinations_client.py) - genuinely free, no API key or signup
# needed. Trade-off: occasional watermark/lower consistency than a paid
# model. If that becomes a problem, the paid fallback is Gemini 3.1 Flash
# Image at roughly $0.04/image.
POLLINATIONS_IMAGE_MODEL = "flux"

# ---- Paths ----
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

# ---- Secrets (read from environment - set these as GitHub Actions secrets) ----
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GUMROAD_ACCESS_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN", "")
