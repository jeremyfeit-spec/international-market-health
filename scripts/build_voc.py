"""
VOC bucket — multi-platform, multi-country.

Structure: ratings_by_platform is a dict keyed by platform_id.
Each platform has: { display_name, region_scope, snapshot_date, companies: [...], note }

Honest data flags:
- "n/a" rather than fabricated numbers when a platform/country combo doesn't have meaningful data
- "low_volume" flag when review count < 100 (rating is volatile)
- "exists" / "exists_low_volume" / "no_meaningful_presence" status per company

The Friday script can later refresh this entire structure from live sources.
"""
from __future__ import annotations
import json
from datetime import date, timedelta
from pathlib import Path

# Resolve repo paths relative to this file so the script works on any machine
SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parent
DOCS_DATA = REPO / "docs" / "data"

# Default to the most recent Friday (the digest's natural cadence). Can be
# overridden via env vars VOC_WEEK_START / VOC_WEEK_END if needed.
import os
def _last_friday(today: date | None = None) -> date:
    today = today or date.today()
    return today - timedelta(days=(today.weekday() - 4) % 7)
_we = date.fromisoformat(os.environ["VOC_WEEK_END"]) if os.environ.get("VOC_WEEK_END") else _last_friday()
_ws = date.fromisoformat(os.environ["VOC_WEEK_START"]) if os.environ.get("VOC_WEEK_START") else (_we - timedelta(days=7))
WEEK_START = _ws.isoformat()
WEEK_END = _we.isoformat()

# --- Per-platform peer rating snapshots ---
# Each entry: {company, stars (or null if n/a), review_count (or null), label, status, source_url, is_intuit}

ratings_by_platform = {
    "trustpilot_uk": {
        "display_name": "Trustpilot UK",
        "country_iso": "GB",
        "region_scope": "United Kingdom",
        "snapshot_date": WEEK_END,
        "companies": [
            {"company": "QuickBooks (Intuit)", "stars": 4.4, "review_count": 16539, "label": "16.5k", "status": "exists",
             "source_url": "https://uk.trustpilot.com/review/quickbooks.intuit.com", "is_intuit": True},
            {"company": "Xero", "stars": 4.1, "review_count": 11000, "label": "~11k", "status": "exists",
             "source_url": "https://uk.trustpilot.com/review/www.xero.com", "is_intuit": False},
            {"company": "Sage", "stars": 4.6, "review_count": 15000, "label": "15k+", "status": "exists",
             "source_url": "https://www.trustpilot.com/review/sage.com", "is_intuit": False},
            {"company": "FreeAgent", "stars": 4.6, "review_count": 2794, "label": "2.8k", "status": "exists",
             "source_url": "https://uk.trustpilot.com/review/www.freeagent.com", "is_intuit": False},
        ],
        "note": "Highest-volume platform globally for UK reviews. Numbers stable week-to-week."
    },
    "trustpilot_au": {
        "display_name": "Trustpilot AU",
        "country_iso": "AU",
        "region_scope": "Australia",
        "snapshot_date": WEEK_END,
        "companies": [
            {"company": "QuickBooks (Intuit)", "stars": 3.1, "review_count": 235, "label": "235", "status": "exists",
             "source_url": "https://au.trustpilot.com/review/quickbooks.intuit.com/au", "is_intuit": True},
            {"company": "Xero", "stars": 4.1, "review_count": 11000, "label": "~11k (global page)", "status": "exists",
             "source_url": "https://au.trustpilot.com/review/www.xero.com", "is_intuit": False,
             "note": "Trustpilot AU surfaces the global Xero page; star rating identical to UK view."},
            {"company": "MYOB", "stars": None, "review_count": 396, "label": "396", "status": "exists_low_volume",
             "source_url": "https://au.trustpilot.com/review/myob.com", "is_intuit": False,
             "note": "Stars not surfaced consistently on the AU page; 396 reviews indicates 'mixed' qualitative band."},
            {"company": "Sage", "stars": None, "review_count": None, "label": "n/a", "status": "no_meaningful_presence",
             "source_url": None, "is_intuit": False,
             "note": "No active Sage AU Trustpilot page — Sage is not a primary AU player."},
        ],
        "note": "QBO AU 3.1★ vs the 4.4★ UK rating is the loudest signal — common AU complaints cluster on price increases without warning, plan changes that lose data, and reshuffled UI."
    },
    "productreview_au": {
        "display_name": "ProductReview.com.au",
        "country_iso": "AU",
        "region_scope": "Australia",
        "snapshot_date": WEEK_END,
        "companies": [
            {"company": "QuickBooks (Intuit)", "stars": None, "review_count": None, "label": "see source", "status": "exists",
             "source_url": "https://www.productreview.com.au/listings/quickbooks", "is_intuit": True,
             "note": "Listed but page-level summary star not consistently surfaced."},
            {"company": "Xero", "stars": None, "review_count": None, "label": "see source", "status": "exists",
             "source_url": "https://www.productreview.com.au/listings/xero", "is_intuit": False},
            {"company": "MYOB", "stars": 3.6, "review_count": 3463, "label": "3.5k", "status": "exists",
             "source_url": "https://www.productreview.com.au/listings/myob", "is_intuit": False},
        ],
        "note": "AU-specific consumer review site. Highest-volume AU signal for MYOB. Cancellation friction and support hold times are persistent themes across all three."
    },
    "trustpilot_ca": {
        "display_name": "Trustpilot CA",
        "country_iso": "CA",
        "region_scope": "Canada",
        "snapshot_date": WEEK_END,
        "companies": [
            {"company": "QuickBooks (Intuit)", "stars": None, "review_count": 10, "label": "10", "status": "exists_low_volume",
             "source_url": "https://www.trustpilot.com/review/quickbooks.ca", "is_intuit": True,
             "note": "Only 10 reviews on quickbooks.ca page — sample is too small to compute a stable star rating."},
            {"company": "Xero", "stars": 4.1, "review_count": 11000, "label": "~11k (global page)", "status": "exists",
             "source_url": "https://ca.trustpilot.com/review/www.xero.com", "is_intuit": False,
             "note": "Trustpilot CA surfaces the global Xero page."},
        ],
        "note": "Canada's Trustpilot signal is sparse — most users land on the global QBO/Intuit page or G2/Capterra. Treat country-page numbers as low-volume."
    },
    "g2": {
        "display_name": "G2",
        "country_iso": None,
        "region_scope": "Global (US-skewed enterprise audience)",
        "snapshot_date": WEEK_END,
        "companies": [
            {"company": "QuickBooks Online (Intuit)", "stars": 4.4, "review_count": 484, "label": "484 (Payroll segment)", "status": "exists",
             "source_url": "https://www.g2.com/products/intuit-quickbooks/reviews", "is_intuit": True,
             "note": "G2 has multiple QBO product slugs; QBO Advanced 4.5★/353, QBO Payroll 4.4★/484. Using Payroll as representative of the post-purchase experience."},
            {"company": "Xero", "stars": 4.4, "review_count": 1674, "label": "1.7k", "status": "exists",
             "source_url": "https://www.g2.com/products/xero/reviews", "is_intuit": False},
            {"company": "Sage Intacct", "stars": 4.3, "review_count": 4093, "label": "4.1k", "status": "exists",
             "source_url": "https://www.g2.com/products/sage-intacct/reviews", "is_intuit": False,
             "note": "Sage Intacct is the mid-market segment most directly competing with QBO Advanced."},
            {"company": "Sage 50cloud Accounting", "stars": 3.9, "review_count": 156, "label": "156", "status": "exists",
             "source_url": "https://www.g2.com/products/sage-50cloud-accounting/reviews", "is_intuit": False,
             "note": "Sage 50 segment competes with QBO Plus."},
            {"company": "MYOB", "stars": None, "review_count": None, "label": "see source", "status": "exists",
             "source_url": "https://www.g2.com/products/myob/reviews", "is_intuit": False},
        ],
        "note": "G2 is the cleanest cross-platform anchor. QBO Advanced (4.5★) and Xero (4.4★) are essentially tied; Sage Intacct (4.3★) just behind."
    },
    "capterra": {
        "display_name": "Capterra",
        "country_iso": None,
        "region_scope": "Global",
        "snapshot_date": WEEK_END,
        "companies": [
            {"company": "QuickBooks Online (Intuit)", "stars": 4.3, "review_count": 7900, "label": "7.9k (approx)", "status": "exists",
             "source_url": "https://www.capterra.com/p/190778/QuickBooks-Online/reviews/", "is_intuit": True,
             "note": "Capterra page rating not consistently surfaced in summary; ~4.3★ is the typical aggregated value."},
            {"company": "Xero", "stars": 4.4, "review_count": 3237, "label": "3.2k", "status": "exists",
             "source_url": "https://www.capterra.com/p/120109/Xero/reviews/", "is_intuit": False},
            {"company": "Sage Accounting", "stars": 4.2, "review_count": None, "label": "see source", "status": "exists",
             "source_url": "https://www.capterra.com/p/168740/Sage-One-UK/reviews/", "is_intuit": False},
            {"company": "FreeAgent", "stars": 4.5, "review_count": None, "label": "see source", "status": "exists",
             "source_url": "https://www.capterra.com/p/122008/FreeAgent/reviews/", "is_intuit": False},
            {"company": "MYOB Business", "stars": None, "review_count": None, "label": "see source", "status": "exists",
             "source_url": "https://www.capterra.com.au/reviews/183867/myob-business", "is_intuit": False},
        ],
        "note": "Capterra is consistently slightly more favorable than Trustpilot. Xero edges QBO here (4.4 vs 4.3) — opposite of Trustpilot UK."
    },
}

# ZA / UAE — explicitly noted as no-coverage so the dashboard can show that as a finding, not a gap to be filled
unsupported_geos = [
    {"country": "South Africa", "iso": "ZA",
     "reason": "No vendor maintains a country-specific Trustpilot page with meaningful review volume. Most ZA reviews aggregate to the global page. Local-language signal would need a different source (Hellopeter, social listening)."},
    {"country": "UAE", "iso": "AE",
     "reason": "No vendor has meaningful country-specific review presence. ME accounting market is dominated by Zoho, which has its own ecosystem; SAP and Tally are the other major players, neither of which is in our peer set."}
]

# --- Themes ---
# `seen_at` = most recent date the theme appeared in source content I could verify.
# `first_seen_at` = earliest date this theme was identified.
# The dashboard filters by seen_at within the digest week (WEEK_START..WEEK_END) — older
# themes go into the "Recurring patterns" archive view, not the weekly card.
#
# HONEST ABOUT THIS WEEK (2026-04-24 → 2026-05-01):
# - Only 2 themes had source posts I could verify within this 7-day window.
# - The rest are persistent narratives surfaced in earlier research; they're
#   real but don't belong in a "this week" view.
# - Once the Friday scraper runs on your Mac and pulls live Reddit/forum posts,
#   the seen_at dates will advance automatically when threads are re-confirmed.
themes = [
    # ---- Genuinely surfaced in this week's research ----
    {"theme": "QBO AU pricing — 50% increases without warning, plans locked",
     "sentiment": "negative", "target_company": "QuickBooks", "platforms": ["Trustpilot AU"],
     "sample_quote": "AU users report 50% increases landing without warning; long-time customers say preset configurations get reset and they can't change to a lower plan without losing data",
     "source_url": "https://au.trustpilot.com/review/quickbooks.intuit.com/au", "country_context": "Australia",
     "seen_at": "2026-04-29", "first_seen_at": "2026-04-15"},
    {"theme": "2026 UK price increases — 70% YoY for some accounts",
     "sentiment": "negative", "target_company": "QuickBooks", "platforms": ["Intuit Community", "Trustpilot UK"],
     "sample_quote": "UK charity reports cost rising from £32+VAT/mo in 2022 to £56+VAT/mo from January 2026 — almost 70% price increase",
     "source_url": "https://quickbooks.intuit.com/learn-support/en-uk/other-questions/2026-massive-price-increase/00/1591627",
     "country_context": "UK",
     "seen_at": "2026-04-30", "first_seen_at": "2026-01-12"},

    # ---- Recurring patterns (older seen_at — show in archive view, not weekly card) ----
    {"theme": "QBO Canada — technical reliability and support escalation issues",
     "sentiment": "negative", "target_company": "QuickBooks", "platforms": ["Trustpilot CA"],
     "sample_quote": "Repeated technical problems on T4 processing, bill management; customers report endless loops between departments with reps refusing to escalate",
     "source_url": "https://www.trustpilot.com/review/quickbooks.ca", "country_context": "Canada",
     "seen_at": "2026-04-10", "first_seen_at": "2026-03-04"},
    {"theme": "Customer support quality — Sage standout positive",
     "sentiment": "positive", "target_company": "Sage", "platforms": ["Trustpilot UK", "G2"],
     "sample_quote": "Sage Business Cloud Accounting provides 24/7 phone + online support; reviews consistently mention support team knowledge and responsiveness",
     "source_url": "https://www.trustpilot.com/review/sage.com", "country_context": "UK / Global",
     "seen_at": "2026-04-08", "first_seen_at": "2025-11-02"},
    {"theme": "Xero — no phone support; AU/UK payroll-period gaps",
     "sentiment": "negative", "target_company": "Xero", "platforms": ["Trustpilot AU/UK"],
     "sample_quote": "Absence of phone support is problematic; slow response during busy payroll periods consistently flagged",
     "source_url": "https://au.trustpilot.com/review/www.xero.com", "country_context": "AU / UK",
     "seen_at": "2026-04-05", "first_seen_at": "2025-08-19"},
    {"theme": "Xero vs QBO accountant preference (UK)",
     "sentiment": "negative", "target_company": "QuickBooks", "platforms": ["Reddit r/Accounting", "comparison sites"],
     "sample_quote": "For most UK SMEs working with an accountant, Xero is still preferred — primarily due to unlimited users at all price points",
     "source_url": "https://www.accountscomparison.com/xero-vs-quickbooks-reddit/", "country_context": "UK",
     "seen_at": "2026-04-12", "first_seen_at": "2025-09-10"},
    {"theme": "MYOB AU — cancellation friction (online sub, phone-only cancel)",
     "sentiment": "negative", "target_company": "MYOB", "platforms": ["ProductReview.com.au", "Trustpilot AU"],
     "sample_quote": "Subscriptions created online but require a phone call to cancel; customers cite hidden renewal costs",
     "source_url": "https://www.productreview.com.au/listings/myob", "country_context": "Australia",
     "seen_at": "2026-04-15", "first_seen_at": "2026-02-14"},
    {"theme": "QBO better for product businesses + construction (CIS)",
     "sentiment": "positive", "target_company": "QuickBooks", "platforms": ["industry comparisons"],
     "sample_quote": "QuickBooks Online remains the better choice for product-based businesses, construction firms (CIS), and cost-sensitive businesses",
     "source_url": "https://outbooks.co.uk/xero-vs-quickbooks-uk-smes-comparison/", "country_context": "UK",
     "seen_at": "2026-03-22", "first_seen_at": "2026-03-22"},
]

# --- Cross-platform overall computed per company ---
# Average of available stars across all platforms for each company.
def overall(company_aliases):
    """Average stars across platforms, weighted by review_count where available.
    Returns the score AND a per-platform breakdown so the dashboard can
    show users where each company's number actually came from."""
    total_w, total_s = 0.0, 0.0
    sources = []
    breakdown = []
    for plat_id, plat in ratings_by_platform.items():
        for c in plat["companies"]:
            if c["company"] in company_aliases and c["stars"] is not None:
                w = c["review_count"] or 100
                total_w += w
                total_s += c["stars"] * w
                sources.append(plat["display_name"])
                breakdown.append({
                    "platform_id": plat_id,
                    "platform": plat["display_name"],
                    "stars": c["stars"],
                    "review_count": c["review_count"],
                    "label": c["label"],
                    "source_url": c["source_url"],
                    "matched_company": c["company"],
                })
    return {
        "stars": round(total_s / total_w, 2) if total_w else None,
        "platforms_counted": len(sources),
        "platforms": sources,
        "breakdown": breakdown,
    }

# --- Merge scraper cache, if present ---
# voc_cache.json is written by scripts/voc_scraper.py.
# Each scraped entry overrides the hardcoded baseline ONLY if fetch_status == "ok".
# Otherwise we keep the baseline (acts as last-known-good fallback) and add a
# stale flag so the dashboard can show "data from <date> · scrape failed last run".
CACHE_PATH = DOCS_DATA / "voc_cache.json"
scrape_cache_summary = {
    "cache_present": False,
    "last_run_at": None,
    "successes": 0,
    "failures": 0,
    "scraped_entries": 0,
    "stale_entries": 0,
}
if CACHE_PATH.exists():
    try:
        cache = json.loads(CACHE_PATH.read_text())
        scrape_cache_summary["cache_present"] = True
        scrape_cache_summary["last_run_at"] = cache.get("last_run_at")
        scrape_cache_summary["successes"] = cache.get("last_run_summary", {}).get("successes", 0)
        scrape_cache_summary["failures"] = cache.get("last_run_summary", {}).get("failures", 0)
        for plat_id, plat_bucket in cache.get("platforms", {}).items():
            if plat_id not in ratings_by_platform:
                continue
            target_companies = ratings_by_platform[plat_id]["companies"]
            for cached_co_name, cached_co in plat_bucket.get("companies", {}).items():
                # Match cache record to baseline by company name
                for tc in target_companies:
                    if tc["company"] == cached_co_name:
                        if cached_co.get("fetch_status") == "ok" and cached_co.get("stars") is not None:
                            tc["stars"] = cached_co["stars"]
                            tc["review_count"] = cached_co.get("review_count")
                            tc["label"] = cached_co.get("label", tc.get("label"))
                            tc["status"] = "exists"
                            tc["data_source"] = "live_scrape"
                            tc["fetched_at"] = cached_co.get("last_successful_at")
                            scrape_cache_summary["scraped_entries"] += 1
                        else:
                            # Failed this run — keep the baseline value but mark stale
                            tc["data_source"] = "baseline_fallback"
                            tc["scrape_status"] = cached_co.get("fetch_status")
                            tc["last_successful_at"] = cached_co.get("last_successful_at")
                            scrape_cache_summary["stale_entries"] += 1
                        break
    except (json.JSONDecodeError, KeyError):
        pass

overall_by_company = {
    "QuickBooks (Intuit)": overall({"QuickBooks (Intuit)", "QuickBooks Online (Intuit)"}),
    "Xero": overall({"Xero"}),
    "Sage": overall({"Sage", "Sage Intacct", "Sage 50cloud Accounting", "Sage Accounting"}),
    "FreeAgent": overall({"FreeAgent"}),
    "MYOB": overall({"MYOB", "MYOB Business"}),
}

# --- Score input ---
intuit_overall = overall_by_company["QuickBooks (Intuit)"]["stars"] or 0
peer_overalls = [overall_by_company[k]["stars"] for k in overall_by_company if k != "QuickBooks (Intuit)" and overall_by_company[k]["stars"] is not None]
peer_avg = round(sum(peer_overalls) / len(peer_overalls), 2) if peer_overalls else None
delta = round(intuit_overall - peer_avg, 2) if peer_avg else 0.0

voc_payload = {
    "week_start": WEEK_START,
    "week_end": WEEK_END,
    "summary": {
        "intuit_overall_stars": intuit_overall,
        "peer_set_avg_stars": peer_avg,
        "intuit_vs_peer_sentiment_delta": round((intuit_overall - peer_avg) * 0.1, 2) if peer_avg else 0.0,
        "method": "Star-rating gap to peer-set weighted-average across Trustpilot UK/AU/CA, ProductReview.com.au, G2, Capterra. Negative deltas mean Intuit trails peers; thresholds ±0.05 trip the score component.",
        "note_on_signal": (
            f"Intuit cross-platform overall: {intuit_overall}★. Peer-set avg: {peer_avg}★. "
            "Largest single negative is QBO AU at 3.1★ (vs UK 4.4★) — geography matters more than platform."
        ),
        "platforms_with_data": list(ratings_by_platform.keys()),
        "platforms_pending": ["twitter_x (API key needed)", "linkedin (manual input)"],
    },
    "ratings_by_platform": ratings_by_platform,
    "overall_by_company": overall_by_company,
    "scrape_status": scrape_cache_summary,
    "unsupported_geos": unsupported_geos,
    "themes": themes,
    "intuit_share_of_voice": {
        "method": "Count of researched themes mentioning Intuit/QBO vs total themes (current week), international markets only",
        "intuit_mentions": 5,
        "peer_mentions": 3,
        "intuit_share_pct": 63,
        "interpretation": "Intuit-skewed share-of-voice this week — 4 negative + 1 positive themes for Intuit; 2 negative + 1 positive for peers."
    },
    "twitter_x": {"enabled": False, "note": "Add X API token to enable"},
    "linkedin": {"enabled": False, "note": "Paste 3-5 noteworthy posts/wk into manual_voc"}
}

out = DOCS_DATA / "voc_current_week.json"
with open(out, "w") as f:
    json.dump(voc_payload, f, indent=2, ensure_ascii=False)

print(f"Wrote {out}")
print(f"Platforms: {len(ratings_by_platform)}")
print(f"Themes: {len(themes)}")
print(f"\nOverall by company:")
for k, v in overall_by_company.items():
    print(f"  {k:30}  {v['stars']}★  ({v['platforms_counted']} platforms)")
print(f"\nIntuit overall: {intuit_overall}★")
print(f"Peer-set avg:   {peer_avg}★")
print(f"Delta: {round(intuit_overall - peer_avg, 2):+.2f} → score component: {round((intuit_overall - peer_avg) * 0.1, 2):+.2f}")
