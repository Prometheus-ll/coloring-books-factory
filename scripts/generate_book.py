"""
Runs the whole "generate" half of the pipeline:

  1. Pick a fresh theme + title + per-page concepts (Gemini text)
  2. Generate the cover illustration + every interior page (Gemini image)
  3. Lay them out into a proper print-ready PDF (cover, numbered pages, back page)
  4. Write the marketplace listing copy (title/description/price) as JSON

Everything lands in output/ as:
  output/coloring_book.pdf   <- the actual product
  output/listing.json        <- what upload_gumroad.py will publish
  output/cover.png           <- quick-look thumbnail for your review

Nothing in this file talks to a selling platform - that's upload_gumroad.py,
which only runs after you approve the review gate.
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

import config
import gemini_client

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
BOLD_FONT_PATH = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
REGULAR_FONT_PATH = os.path.join(FONT_DIR, "DejaVuSans.ttf")


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        # Falls back to PIL's built-in bitmap font if DejaVu isn't installed.
        # Ugly but never crashes the run over a missing font package.
        return ImageFont.load_default()


def plan_book() -> dict:
    prompt = f"""You invent one-off coloring book concepts for a print-on-demand shop.

Invent ONE fresh, specific coloring book theme - not a generic one you'd expect
every day (avoid plain "animals" or "flowers" on their own; go for a specific
angle, e.g. "underwater creatures having a tea party" or "tiny robots gardening").
It should be family-friendly and suitable for {config.AUDIENCE_HINT}.

Then write exactly {config.NUM_INTERIOR_PAGES} distinct page concepts for it -
each a short (under 12 words) description of a single scene or subject to
illustrate as a coloring page. No two pages should be near-duplicates.

Respond with ONLY raw JSON, no markdown fences, in exactly this shape:
{{
  "theme": "short theme name",
  "title": "a catchy 3-6 word book title",
  "pages": ["page 1 concept", "page 2 concept", "... exactly {config.NUM_INTERIOR_PAGES} items"]
}}"""
    plan = gemini_client.generate_json(prompt)
    if not plan.get("pages"):
        raise RuntimeError(f"Book plan came back without pages: {plan}")
    return plan


def plan_listing_copy(theme: str, title: str, num_pages: int) -> dict:
    prompt = f"""Write marketplace listing copy for a printable digital coloring book PDF.

Theme: {theme}
Title: {title}
Page count: {num_pages} coloring pages plus a cover.

Respond with ONLY raw JSON, no markdown fences, in exactly this shape:
{{
  "title": "SEO-friendly product title, under 80 characters",
  "short_description": "one punchy sentence",
  "long_description": "3-5 sentences a buyer would read on the product page, plain text, no markdown",
  "tags": ["8 to 13 relevant lowercase search tags as an array of strings"]
}}"""
    return gemini_client.generate_json(prompt)


def coloring_page_prompt(concept: str) -> str:
    return (
        f"Black-and-white line art coloring book page for {config.AUDIENCE_HINT}. "
        f"Subject: {concept}. Bold, clean, fully closed outlines suitable for "
        f"coloring with crayons or markers. Pure black lines on a pure white "
        f"background. No shading, no gray fill, no color, no text, no watermark, "
        f"no signature, no border frame."
    )


def cover_illustration_prompt(theme: str) -> str:
    return (
        f"Black-and-white line art illustration for a coloring book cover. "
        f"Theme: {theme}. Bold clean outlines, no shading, no gray fill, no "
        f"color, no text, no watermark. Centered composition with open space "
        f"near the top and bottom of the frame for a title to be added later."
    )


def _fit_and_paste(canvas: Image.Image, art: Image.Image, box):
    left, top, right, bottom = box
    box_w, box_h = right - left, bottom - top
    art_ratio = art.width / art.height
    box_ratio = box_w / box_h
    if art_ratio > box_ratio:
        new_w = box_w
        new_h = int(box_w / art_ratio)
    else:
        new_h = box_h
        new_w = int(box_h * art_ratio)
    art_resized = art.resize((new_w, new_h), Image.LANCZOS)
    paste_x = left + (box_w - new_w) // 2
    paste_y = top + (box_h - new_h) // 2
    canvas.paste(art_resized, (paste_x, paste_y))


def build_interior_page(art: Image.Image, page_number: int) -> Image.Image:
    canvas = Image.new("RGB", (config.PAGE_WIDTH_PX, config.PAGE_HEIGHT_PX), "white")
    draw = ImageDraw.Draw(canvas)
    art_box = (
        config.MARGIN_PX,
        config.MARGIN_PX,
        config.PAGE_WIDTH_PX - config.MARGIN_PX,
        config.PAGE_HEIGHT_PX - config.MARGIN_PX - 100,
    )
    _fit_and_paste(canvas, art, art_box)
    font = _font(REGULAR_FONT_PATH, config.PAGE_NUMBER_FONT_SIZE)
    number_text = str(page_number)
    bbox = draw.textbbox((0, 0), number_text, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(
        ((config.PAGE_WIDTH_PX - text_w) / 2, config.PAGE_HEIGHT_PX - config.MARGIN_PX),
        number_text,
        fill="black",
        font=font,
    )
    return canvas


def build_cover(art: Image.Image, title: str) -> Image.Image:
    canvas = Image.new("RGB", (config.PAGE_WIDTH_PX, config.PAGE_HEIGHT_PX), "white")
    draw = ImageDraw.Draw(canvas)
    art_box = (
        config.MARGIN_PX,
        int(config.PAGE_HEIGHT_PX * 0.28),
        config.PAGE_WIDTH_PX - config.MARGIN_PX,
        int(config.PAGE_HEIGHT_PX * 0.85),
    )
    _fit_and_paste(canvas, art, art_box)

    title_font = _font(BOLD_FONT_PATH, config.COVER_TITLE_FONT_SIZE)
    # Wrap the title across a couple of lines if it's long, so it never
    # runs off the page width.
    words = title.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=title_font)[2] > config.PAGE_WIDTH_PX - 2 * config.MARGIN_PX:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)

    y = int(config.PAGE_HEIGHT_PX * 0.08)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        draw.text(((config.PAGE_WIDTH_PX - line_w) / 2, y), line, fill="black", font=title_font)
        y += line_h + 20

    subtitle_font = _font(REGULAR_FONT_PATH, config.COVER_SUBTITLE_FONT_SIZE)
    subtitle = "A Coloring Book"
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_w = bbox[2] - bbox[0]
    draw.text(
        ((config.PAGE_WIDTH_PX - sub_w) / 2, config.PAGE_HEIGHT_PX - config.MARGIN_PX - 60),
        subtitle,
        fill="black",
        font=subtitle_font,
    )
    return canvas


def build_back_page() -> Image.Image:
    canvas = Image.new("RGB", (config.PAGE_WIDTH_PX, config.PAGE_HEIGHT_PX), "white")
    draw = ImageDraw.Draw(canvas)
    font = _font(BOLD_FONT_PATH, 70)
    text = "Thank You For Coloring!"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(
        ((config.PAGE_WIDTH_PX - text_w) / 2, config.PAGE_HEIGHT_PX / 2 - 40),
        text,
        fill="black",
        font=font,
    )
    return canvas


def main():
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    print("Planning today's book...")
    plan = plan_book()
    theme, title, page_concepts = plan["theme"], plan["title"], plan["pages"]
    print(f"Theme: {theme}\nTitle: {title}\nPages planned: {len(page_concepts)}")

    print("Generating cover illustration...")
    cover_art = gemini_client.generate_image(cover_illustration_prompt(theme))
    cover_page = build_cover(cover_art, title)
    cover_page.save(os.path.join(config.OUTPUT_DIR, "cover.png"))

    interior_pages = []
    for i, concept in enumerate(page_concepts, start=1):
        print(f"Generating page {i}/{len(page_concepts)}: {concept}")
        try:
            art = gemini_client.generate_image(coloring_page_prompt(concept))
        except Exception as e:  # noqa: BLE001 - keep the whole book from failing over one page
            print(f"  Page {i} failed ({e}); leaving it blank rather than stopping the run.")
            art = Image.new("RGB", (1024, 1024), "white")
        interior_pages.append(build_interior_page(art, i))

    back_page = build_back_page()

    all_pages = [cover_page] + interior_pages + [back_page]
    pdf_path = os.path.join(config.OUTPUT_DIR, "coloring_book.pdf")
    all_pages[0].save(pdf_path, save_all=True, append_images=all_pages[1:])
    print(f"Saved PDF: {pdf_path} ({len(all_pages)} pages total)")

    print("Writing listing copy...")
    listing_copy = plan_listing_copy(theme, title, len(page_concepts))
    listing = {
        "title": listing_copy.get("title", title),
        "short_description": listing_copy.get("short_description", ""),
        "long_description": listing_copy.get("long_description", ""),
        "tags": listing_copy.get("tags", []),
        "price_usd": config.PRICE_USD,
        "theme": theme,
        "page_count": len(page_concepts),
    }
    with open(os.path.join(config.OUTPUT_DIR, "listing.json"), "w") as f:
        json.dump(listing, f, indent=2)

    summary = (
        f"### Today's coloring book: {listing['title']}\n\n"
        f"- Theme: {theme}\n"
        f"- Pages: {len(page_concepts)} + cover\n"
        f"- Price: ${config.PRICE_USD}\n\n"
        f"Download the `coloring-book` artifact from this run to preview the "
        f"actual PDF before approving the upload step.\n"
    )
    print(summary)
    step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary_path:
        with open(step_summary_path, "a") as f:
            f.write(summary)


if __name__ == "__main__":
    main()
