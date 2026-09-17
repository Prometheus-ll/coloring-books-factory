"""
All the settings you're likely to want to tweak live here, in one place.
Nothing in this file is secret - API keys come from environment variables
(set as GitHub Actions secrets), never hardcoded here.
"""

import os

# ---- Content ----
NUM_INTERIOR_PAGES = 24          # how many coloring pages per book (not counting cover)
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

# ---- Gemini models ----
# Free-tier models as of writing. If Google renames/retires one of these,
# this is the only place you need to change it.
TEXT_MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"

# ---- Paths ----
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

# ---- Secrets (read from environment - set these as GitHub Actions secrets) ----
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GUMROAD_ACCESS_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN", "")
