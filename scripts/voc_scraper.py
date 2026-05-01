"""
VOC scraper — best-effort live fetch of peer ratings across platforms.

Design principles:
- Honest about what worked vs what didn't. Each (platform, company) entry
  carries fetch_status, fetched_at, last_successful_at.
- Never invent data. If we can't parse a number, we leave the previous
  value with a stale flag.
- Designed to run on the user's Mac during the Friday cron job, where
  the proxy allowlist that blocks reddit.com / trustpilot.com inside
  the Cowork sandbox doesn't apply.
- Single source of truth: docs/data/voc_cache.json. The Friday digest
  builder reads this and merges into super_digest.json.

Usage:
    python3 scripts/voc_scraper.py            # scrape everything
    python3 scripts/voc_scraper.py --platform trustpilot_uk
    python3 scripts/voc_scraper.py --dry-run  # don't write cache, just print
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

REPO = Path(__file__).resolve().parent.parent
CACHE_PATH = REPO / "docs" / "data" / "voc_cache.json"
CONFIG_PATH = REPO / "config" / "dashboard.json"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Safari/605.1.15"
)
REQUEST_TIMEOUT = 15  # seconds
BETWEEN_REQUESTS_SECONDS = 1.5  # be polite

# ---------------------------------------------------------------------------
# Targets — each entry is one (platform, company) fetch.
# Each platform has its own parser keyed by platform_id. New platforms can
# be added without changing the runner.
# ---------------------------------------------------------------------------
TARGETS = [
    # Trustpilot UK
    {"platform_id": "trustpilot_uk", "company": "QuickBooks (Intuit)", "url": "https://uk.trustpilot.com/review/quickbooks.intuit.com", "is_intuit": True},
    {"platform_id": "trustpilot_uk", "company": "Xero",                "url": "https://uk.trustpilot.com/review/www.xero.com"},
    {"platform_id": "trustpilot_uk", "company": "Sage",                "url": "https://www.trustpilot.com/review/sage.com"},
    {"platform_id": "trustpilot_uk", "company": "FreeAgent",           "url": "https://uk.trustpilot.com/review/www.freeagent.com"},

    # Trustpilot AU
    {"platform_id": "trustpilot_au", "company": "QuickBooks (Intuit)", "url": "https://au.trustpilot.com/review/quickbooks.intuit.com/au", "is_intuit": True},
    {"platform_id": "trustpilot_au", "company": "Xero",                "url": "https://au.trustpilot.com/review/www.xero.com"},
    {"platform_id": "trustpilot_au", "company": "MYOB",                "url": "https://au.trustpilot.com/review/myob.com"},

    # Trustpilot CA
    {"platform_id": "trustpilot_ca", "company": "QuickBooks (Intuit)", "url": "https://www.trustpilot.com/review/quickbooks.ca", "is_intuit": True},
    {"platform_id": "trustpilot_ca", "company": "Xero",                "url": "https://ca.trustpilot.com/review/www.xero.com"},

    # ProductReview.com.au
    {"platform_id": "productreview_au", "company": "QuickBooks (Intuit)", "url": "https://www.productreview.com.au/listings/quickbooks", "is_intuit": True},
    {"platform_id": "productreview_au", "company": "Xero",                "url": "https://www.productreview.com.au/listings/xero"},
    {"platform_id": "productreview_au", "company": "MYOB",                "url": "https://www.productreview.com.au/listings/myob"},

    # G2
    {"platform_id": "g2", "company": "QuickBooks Online (Intuit)", "url": "https://www.g2.com/products/intuit-quickbooks/reviews", "is_intuit": True},
    {"platform_id": "g2", "company": "Xero",                       "url": "https://www.g2.com/products/xero/reviews"},
    {"platform_id": "g2", "company": "Sage Intacct",               "url": "https://www.g2.com/products/sage-intacct/reviews"},
    {"platform_id": "g2", "company": "Sage 50cloud Accounting",    "url": "https://www.g2.com/products/sage-50cloud-accounting/reviews"},
    {"platform_id": "g2", "company": "MYOB",                       "url": "https://www.g2.com/products/myob/reviews"},

    # Capterra
    {"platform_id": "capterra", "company": "QuickBooks Online (Intuit)", "url": "https://www.capterra.com/p/190778/QuickBooks-Online/reviews/", "is_intuit": True},
    {"platform_id": "capterra", "company": "Xero",                       "url": "https://www.capterra.com/p/120109/Xero/reviews/"},
    {"platform_id": "capterra", "company": "Sage Accounting",            "url": "https://www.capterra.com/p/168740/Sage-One-UK/reviews/"},
    {"platform_id": "capterra", "company": "FreeAgent",                  "url": "https://www.capterra.com/p/122008/FreeAgent/reviews/"},
]

# ---------------------------------------------------------------------------
# Per-platform parsers
# ---------------------------------------------------------------------------

def fetch_html(url: str) -> tuple[Optional[str], Optional[str]]:
    """Returns (html, error_str). Either may be None."""
    try:
        r = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-GB,en;q=0.9",
                "Cache-Control": "no-cache",
            },
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        if len(r.text) < 1000:
            return None, "response_too_short"
        return r.text, None
    except requests.exceptions.Timeout:
        return None, "timeout"
    except requests.exceptions.RequestException as e:
        return None, f"request_error: {type(e).__name__}"


def _to_int(s: str) -> Optional[int]:
    if not s:
        return None
    s = s.replace(",", "").replace(" ", "").strip().lower()
    # "16k", "1.5k", "11k+"
    m = re.match(r"^([\d.]+)\s*([km])\+?$", s)
    if m:
        n, unit = float(m.group(1)), m.group(2)
        return int(n * (1000 if unit == "k" else 1_000_000))
    if s.replace(".", "").isdigit():
        try:
            return int(float(s))
        except ValueError:
            return None
    return None


def parse_trustpilot(html: str) -> dict:
    """Trustpilot embeds a JSON-LD AggregateRating block on every review page.
    Falls back to scraping the rendered numbers if JSON-LD isn't present."""
    soup = BeautifulSoup(html, "html.parser")

    # Path 1: schema.org JSON-LD
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            blob = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = blob if isinstance(blob, list) else [blob]
        for item in items:
            if not isinstance(item, dict):
                continue
            agg = item.get("aggregateRating") or {}
            if "ratingValue" in agg or "reviewCount" in agg:
                stars = agg.get("ratingValue")
                count = agg.get("reviewCount") or agg.get("ratingCount")
                if stars is not None:
                    return {
                        "stars": float(stars),
                        "review_count": int(count) if count else None,
                        "method": "json-ld",
                    }
            # Sometimes nested under @graph
            for sub in item.get("@graph", []) or []:
                agg = sub.get("aggregateRating") or {}
                if "ratingValue" in agg:
                    return {
                        "stars": float(agg["ratingValue"]),
                        "review_count": int(agg.get("reviewCount") or agg.get("ratingCount") or 0) or None,
                        "method": "json-ld-graph",
                    }

    # Path 2: rendered numbers — TrustScore
    # e.g. <p class="typography_body-l...">TrustScore <span>4.4</span> | <span>16,539</span> reviews</p>
    text = soup.get_text(" ", strip=True)
    star_match = re.search(r"TrustScore\s*([\d.]+)", text)
    count_match = re.search(r"([\d,]+)\s+reviews?", text)
    if star_match:
        return {
            "stars": float(star_match.group(1)),
            "review_count": _to_int(count_match.group(1)) if count_match else None,
            "method": "rendered-text",
        }
    return {"stars": None, "review_count": None, "method": None}


def parse_productreview_au(html: str) -> dict:
    """ProductReview.com.au has aggregateRating in JSON-LD on listing pages."""
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            blob = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = blob if isinstance(blob, list) else [blob]
        for item in items:
            agg = (item.get("aggregateRating") if isinstance(item, dict) else None) or {}
            if "ratingValue" in agg:
                return {
                    "stars": float(agg["ratingValue"]),
                    "review_count": int(agg.get("reviewCount") or agg.get("ratingCount") or 0) or None,
                    "method": "json-ld",
                }
    return {"stars": None, "review_count": None, "method": None}


def parse_g2(html: str) -> dict:
    """G2 uses JSON-LD on review pages with aggregateRating.
    G2 has aggressive bot detection — failures here are expected."""
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            blob = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = blob if isinstance(blob, list) else [blob]
        for item in items:
            if not isinstance(item, dict):
                continue
            agg = item.get("aggregateRating") or {}
            if "ratingValue" in agg:
                return {
                    "stars": float(agg["ratingValue"]),
                    "review_count": int(agg.get("reviewCount") or agg.get("ratingCount") or 0) or None,
                    "method": "json-ld",
                }
    # Fallback: rendered "4.4 out of 5" pattern
    text = soup.get_text(" ", strip=True)
    m = re.search(r"([\d.]+)\s*out of 5\s*stars?", text, re.IGNORECASE)
    if m:
        count_m = re.search(r"\(([\d,]+)\s+reviews?\)", text)
        return {
            "stars": float(m.group(1)),
            "review_count": _to_int(count_m.group(1)) if count_m else None,
            "method": "rendered-text",
        }
    return {"stars": None, "review_count": None, "method": None}


def parse_capterra(html: str) -> dict:
    """Capterra uses JSON-LD too. Heavy CDN/bot protection — best-effort."""
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            blob = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = blob if isinstance(blob, list) else [blob]
        for item in items:
            if not isinstance(item, dict):
                continue
            agg = item.get("aggregateRating") or {}
            if "ratingValue" in agg:
                return {
                    "stars": float(agg["ratingValue"]),
                    "review_count": int(agg.get("reviewCount") or agg.get("ratingCount") or 0) or None,
                    "method": "json-ld",
                }
    return {"stars": None, "review_count": None, "method": None}


PARSERS = {
    "trustpilot_uk": parse_trustpilot,
    "trustpilot_au": parse_trustpilot,
    "trustpilot_ca": parse_trustpilot,
    "productreview_au": parse_productreview_au,
    "g2": parse_g2,
    "capterra": parse_capterra,
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except json.JSONDecodeError:
            pass
    return {"version": 1, "platforms": {}}


def save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False))


def humanize_count(n: Optional[int]) -> str:
    if n is None:
        return "?"
    if n >= 10_000:
        return f"{n // 1000}k"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def run_scrape(filter_platform: Optional[str] = None, dry_run: bool = False) -> dict:
    cache = load_cache()
    cache.setdefault("platforms", {})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    cache["last_run_at"] = now

    successes, failures = 0, 0

    for target in TARGETS:
        plat = target["platform_id"]
        if filter_platform and plat != filter_platform:
            continue
        company = target["company"]
        url = target["url"]
        parser = PARSERS.get(plat)
        if not parser:
            continue

        # Locate or create the company record in the cache
        plat_bucket = cache["platforms"].setdefault(plat, {"companies": {}})
        rec = plat_bucket["companies"].setdefault(company, {
            "company": company, "url": url, "is_intuit": target.get("is_intuit", False),
        })

        print(f"[{plat:18}] {company[:36]:36}  ", end="", flush=True)

        html, fetch_err = fetch_html(url)
        if fetch_err:
            rec["fetched_at"] = now
            rec["fetch_status"] = "fetch_failed"
            rec["fetch_error"] = fetch_err
            failures += 1
            print(f"FAIL · {fetch_err}")
            time.sleep(BETWEEN_REQUESTS_SECONDS)
            continue

        parsed = parser(html)
        if parsed.get("stars") is None and parsed.get("review_count") is None:
            rec["fetched_at"] = now
            rec["fetch_status"] = "parse_failed"
            failures += 1
            print(f"PARSE FAIL · response received but no numbers extracted")
            time.sleep(BETWEEN_REQUESTS_SECONDS)
            continue

        # Success: update fields, record timestamp
        rec["stars"] = parsed.get("stars")
        rec["review_count"] = parsed.get("review_count")
        rec["label"] = humanize_count(parsed.get("review_count"))
        rec["fetched_at"] = now
        rec["last_successful_at"] = now
        rec["parse_method"] = parsed.get("method")
        rec["fetch_status"] = "ok"
        rec["url"] = url
        rec["is_intuit"] = target.get("is_intuit", False)
        successes += 1
        stars_s = f"{parsed['stars']}★" if parsed.get("stars") is not None else "—"
        count_s = humanize_count(parsed.get("review_count"))
        print(f"OK    · {stars_s} ({count_s}) via {parsed.get('method')}")
        time.sleep(BETWEEN_REQUESTS_SECONDS)

    cache["last_run_summary"] = {"successes": successes, "failures": failures, "ran_at": now}
    print(f"\n--- {successes} OK, {failures} failed/parse-failed ---")

    if not dry_run:
        save_cache(cache)
        print(f"Wrote {CACHE_PATH.relative_to(REPO)}")
    else:
        print("(dry-run — cache not written)")

    return cache


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", help="Limit to one platform_id (e.g. trustpilot_uk)")
    parser.add_argument("--dry-run", action="store_true", help="Don't write cache file")
    args = parser.parse_args()
    run_scrape(filter_platform=args.platform, dry_run=args.dry_run)
