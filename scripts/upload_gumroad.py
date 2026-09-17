"""
Publishes output/coloring_book.pdf + output/listing.json as a live Gumroad
product. This only runs in the "upload" job, which sits behind the
protected "production" environment - so it only fires after you approve it.

Heads-up: Gumroad's product-creation API is fairly new (added April 2026)
and its public docs page is JS-rendered, so I couldn't machine-verify every
exact field name here. The overall flow (presign -> upload -> complete ->
create product -> publish) is right, but if a call fails, the printed
response body will show exactly what Gumroad expected - paste that back to
me and this file is a one-function fix.
"""

import json
import os

import requests

import config

API_BASE = "https://api.gumroad.com/v2"


def _check(resp: requests.Response, step: str) -> dict:
    if not resp.ok:
        raise RuntimeError(f"Gumroad step '{step}' failed: HTTP {resp.status_code}\n{resp.text}")
    return resp.json()


def upload_file(pdf_path: str) -> dict:
    filename = os.path.basename(pdf_path)
    file_size = os.path.getsize(pdf_path)

    presign = _check(
        requests.post(
            f"{API_BASE}/files/presign",
            data={
                "access_token": config.GUMROAD_ACCESS_TOKEN,
                "filename": filename,
                "file_size": file_size,
            },
            timeout=60,
        ),
        "presign",
    )

    upload_url = presign.get("presigned_url") or presign.get("url")
    if not upload_url:
        raise RuntimeError(f"Presign response had no upload URL - raw response:\n{presign}")

    with open(pdf_path, "rb") as f:
        put_resp = requests.put(upload_url, data=f, timeout=300)
    if not put_resp.ok:
        raise RuntimeError(f"File upload PUT failed: HTTP {put_resp.status_code}\n{put_resp.text}")
    etag = put_resp.headers.get("ETag", "")

    complete = _check(
        requests.post(
            f"{API_BASE}/files/complete",
            data={
                "access_token": config.GUMROAD_ACCESS_TOKEN,
                "upload_id": presign.get("upload_id"),
                "key": presign.get("key"),
                "parts[][part_number]": 1,
                "parts[][etag]": etag,
            },
            timeout=120,
        ),
        "complete",
    )
    return complete


def create_product(listing: dict, uploaded_file: dict) -> dict:
    payload = {
        "access_token": config.GUMROAD_ACCESS_TOKEN,
        "name": listing["title"],
        "description": listing["long_description"],
        "price": int(round(listing["price_usd"] * 100)),  # Gumroad wants cents
    }
    file_id = uploaded_file.get("id") or uploaded_file.get("file_id")
    if file_id:
        payload["file_id"] = file_id

    product = _check(
        requests.post(f"{API_BASE}/products", data=payload, timeout=60),
        "create product",
    )
    return product


def publish_product(product_id: str) -> dict:
    return _check(
        requests.put(
            f"{API_BASE}/products/{product_id}",
            data={"access_token": config.GUMROAD_ACCESS_TOKEN, "published": "true"},
            timeout=60,
        ),
        "publish",
    )


def main():
    pdf_path = os.path.join(config.OUTPUT_DIR, "coloring_book.pdf")
    listing_path = os.path.join(config.OUTPUT_DIR, "listing.json")

    with open(listing_path) as f:
        listing = json.load(f)

    print(f"Uploading {pdf_path} to Gumroad...")
    uploaded_file = upload_file(pdf_path)

    print(f"Creating product: {listing['title']} (${listing['price_usd']})")
    product = create_product(listing, uploaded_file)
    product_id = product.get("id") or product.get("product", {}).get("id")

    print("Publishing...")
    published = publish_product(product_id)
    url = published.get("short_url") or published.get("url") or "(check your Gumroad dashboard for the link)"

    summary = f"### Published: {listing['title']}\n\n{url}\n"
    print(summary)
    step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary_path:
        with open(step_summary_path, "a") as f:
            f.write(summary)


if __name__ == "__main__":
    main()
